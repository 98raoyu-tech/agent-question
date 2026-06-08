"""
统一追踪器模块

提供面向所有模块类型的统一追踪能力，集成TracingManager和TraceContext，
通过contextvars实现异步安全的上下文传播。
"""

import asyncio
import contextvars
import logging
import uuid
from collections.abc import Callable
from typing import Any

from .trace_context import TraceContext
from .tracing import TracingManager, tracing_manager

logger = logging.getLogger(__name__)

# 异步安全的追踪上下文存储
_trace_context_var: contextvars.ContextVar[TraceContext | None] = (
    contextvars.ContextVar("trace_context", default=None)
)


class UnifiedTracer:
    """统一追踪器

    为Agent、工作流、工具调用、评估和流水线等所有模块类型
    提供一致的追踪接口，内部复用TracingManager的OpenTelemetry能力。
    """

    def __init__(
        self,
        manager: TracingManager | None = None,
    ) -> None:
        """初始化统一追踪器

        Args:
            manager: TracingManager实例，默认使用全局单例
        """
        self._manager: TracingManager = manager or tracing_manager

    def get_current_context(self) -> TraceContext | None:
        """获取当前追踪上下文

        Returns:
            当前上下文中的TraceContext，不存在则返回None
        """
        return _trace_context_var.get(None)

    def set_current_context(self, context: TraceContext) -> None:
        """设置当前追踪上下文

        Args:
            context: 要设置的追踪上下文
        """
        _trace_context_var.set(context)

    def _build_context(
        self,
        *,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        pipeline_id: str | None = None,
        tenant_id: str | None = None,
        project_id: str | None = None,
    ) -> TraceContext:
        """基于当前上下文构建子级上下文

        若当前已有上下文则继承trace_id，否则创建全新的上下文。

        Returns:
            新的追踪上下文实例
        """
        parent = self.get_current_context()
        new_span_id = uuid.uuid4().hex[:16]

        if parent is not None:
            child_ctx = parent.child(new_span_id)
            # 补充当前调用特有的标识
            if agent_id is not None:
                child_ctx.agent_id = agent_id
            if workflow_id is not None:
                child_ctx.workflow_id = workflow_id
            if pipeline_id is not None:
                child_ctx.pipeline_id = pipeline_id
            return child_ctx

        return TraceContext(
            trace_id=uuid.uuid4().hex,
            span_id=new_span_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            pipeline_id=pipeline_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )

    def _execute_traced(
        self,
        span_name: str,
        context: TraceContext,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """在追踪Span内执行函数

        同时设置TraceContext和OpenTelemetry Span，保证两种追踪机制
        都能正确记录。同步与异步函数均支持。

        Args:
            span_name: Span名称
            context: 追踪上下文
            func: 被追踪的目标函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            目标函数的返回值
        """
        attributes = {
            k: v
            for k, v in context.to_dict().items()
            if k not in ("trace_id", "span_id")
        }

        # 设置上下文
        token = _trace_context_var.set(context)

        try:
            # 判断是否为异步函数
            if asyncio.iscoroutinefunction(func):
                return self._async_traced(span_name, attributes, func, *args, **kwargs)

            with self._manager.trace_operation(span_name, attributes):
                return func(*args, **kwargs)
        finally:
            _trace_context_var.reset(token)

    async def _async_traced(
        self,
        span_name: str,
        attributes: dict[str, str],
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """在追踪Span内执行异步函数

        Args:
            span_name: Span名称
            attributes: Span属性
            func: 异步目标函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            目标函数的返回值
        """
        with self._manager.trace_operation(span_name, attributes):
            return await func(*args, **kwargs)

    def trace_agent_operation(
        self,
        agent_id: str,
        operation: str,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """追踪Agent操作

        Args:
            agent_id: Agent标识
            operation: 操作类型描述
            func: 被追踪的目标函数
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数

        Returns:
            目标函数的返回值
        """
        context = self._build_context(agent_id=agent_id)
        span_name = f"agent.{agent_id}.{operation}"
        return self._execute_traced(span_name, context, func, *args, **kwargs)

    def trace_workflow_execution(
        self,
        workflow_id: str,
        node_id: str,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """追踪工作流执行

        Args:
            workflow_id: 工作流标识
            node_id: 节点标识
            func: 被追踪的目标函数
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数

        Returns:
            目标函数的返回值
        """
        context = self._build_context(workflow_id=workflow_id)
        span_name = f"workflow.{workflow_id}.node.{node_id}"
        return self._execute_traced(span_name, context, func, *args, **kwargs)

    def trace_tool_invocation(
        self,
        tool_id: str,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """追踪工具调用

        Args:
            tool_id: 工具标识
            func: 被追踪的目标函数
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数

        Returns:
            目标函数的返回值
        """
        context = self._build_context()
        span_name = f"tool.{tool_id}.invoke"
        return self._execute_traced(span_name, context, func, *args, **kwargs)

    def trace_evaluation(
        self,
        evaluation_id: str,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """追踪评估执行

        Args:
            evaluation_id: 评估标识
            func: 被追踪的目标函数
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数

        Returns:
            目标函数的返回值
        """
        context = self._build_context()
        span_name = f"evaluation.{evaluation_id}.execute"
        return self._execute_traced(span_name, context, func, *args, **kwargs)

    def trace_pipeline_step(
        self,
        pipeline_id: str,
        stage: str,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """追踪流水线步骤

        Args:
            pipeline_id: 流水线标识
            stage: 阶段名称
            func: 被追踪的目标函数
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数

        Returns:
            目标函数的返回值
        """
        context = self._build_context(pipeline_id=pipeline_id)
        span_name = f"pipeline.{pipeline_id}.stage.{stage}"
        return self._execute_traced(span_name, context, func, *args, **kwargs)


# 全局统一追踪器实例
unified_tracer = UnifiedTracer()
