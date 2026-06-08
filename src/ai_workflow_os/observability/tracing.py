"""
OpenTelemetry链路追踪模块

集成OpenTelemetry的分布式链路追踪，支持Span创建、指标记录和事件添加。
"""

import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, StatusCode

logger = logging.getLogger(__name__)


class TracingManager:
    """OpenTelemetry链路追踪管理器"""

    def __init__(self) -> None:
        """初始化追踪管理器"""
        self._tracer: Optional[trace.Tracer] = None
        self._provider: Optional[TracerProvider] = None
        self._initialized: bool = False

    def initialize(
        self,
        service_name: str = "ai-workflow-os",
        exporter: Optional[Any] = None,
    ) -> None:
        """初始化OpenTelemetry

        Args:
            service_name: 服务名称
            exporter: Span导出器，默认使用控制台导出器
        """
        if self._initialized:
            logger.warning("追踪管理器已初始化，跳过重复初始化")
            return

        # 创建TracerProvider
        self._provider = TracerProvider(resource=None)

        # 添加Span处理器
        if exporter is None:
            exporter = ConsoleSpanExporter()

        span_processor = BatchSpanProcessor(exporter)
        self._provider.add_span_processor(span_processor)

        # 设置全局TracerProvider
        trace.set_tracer_provider(self._provider)

        # 获取Tracer
        self._tracer = trace.get_tracer(service_name)
        self._initialized = True

        logger.info(f"追踪管理器初始化完成，服务名: {service_name}")

    @property
    def tracer(self) -> trace.Tracer:
        """获取Tracer实例

        Returns:
            OpenTelemetry Tracer实例

        Raises:
            RuntimeError: 管理器未初始化
        """
        if self._tracer is None:
            raise RuntimeError("追踪管理器未初始化，请先调用 initialize()")
        return self._tracer

    def start_span(
        self,
        name: str,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Span:
        """开始一个新的Span

        Args:
            name: Span名称
            attributes: Span属性字典

        Returns:
            创建的Span实例
        """
        span = self.tracer.start_span(name)

        # 设置属性
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    @contextmanager
    def trace_operation(
        self,
        name: str,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """追踪操作的上下文管理器

        自动管理Span的生命周期，包括异常处理。

        Args:
            name: 操作名称
            attributes: Span属性字典

        Yields:
            Span实例
        """
        with self.tracer.start_as_current_span(name) as span:
            # 设置属性
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as e:
                # 记录异常信息
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    def record_metric(
        self,
        name: str,
        value: float,
        attributes: Optional[dict[str, Any]] = None,
    ) -> None:
        """记录指标

        Args:
            name: 指标名称
            value: 指标值
            attributes: 指标属性
        """
        # TODO: 集成OpenTelemetry Metrics
        logger.debug(f"记录指标: {name}={value}, 属性={attributes}")

    def add_event(
        self,
        name: str,
        attributes: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加事件到当前Span

        Args:
            name: 事件名称
            attributes: 事件属性
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes or {})

    def set_span_attribute(self, key: str, value: Any) -> None:
        """设置当前Span的属性

        Args:
            key: 属性键
            value: 属性值
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)

    def create_trace_context(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ) -> dict[str, str]:
        """创建追踪上下文（用于跨服务传播）

        Args:
            trace_id: 追踪ID，为None时使用当前追踪ID
            span_id: Span ID，为None时使用当前Span ID

        Returns:
            追踪上下文字典
        """
        current_span = trace.get_current_span()
        context = {}

        if current_span:
            span_context = current_span.get_span_context()
            context["trace_id"] = trace_id or format(span_context.trace_id, "032x")
            context["span_id"] = span_id or format(span_context.span_id, "016x")
            context["trace_flags"] = format(span_context.trace_flags, "02x")
        else:
            context["trace_id"] = trace_id or "00000000000000000000000000000000"
            context["span_id"] = span_id or "0000000000000000"
            context["trace_flags"] = "00"

        return context

    def shutdown(self) -> None:
        """关闭追踪管理器，清理资源"""
        if self._provider:
            self._provider.shutdown()
            self._initialized = False
            logger.info("追踪管理器已关闭")


# 全局追踪管理器实例
tracing_manager = TracingManager()


def traced(operation_name: Optional[str] = None) -> Callable:
    """自动追踪函数调用的装饰器

    Args:
        operation_name: 操作名称，默认使用函数名

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__qualname__}"
            with tracing_manager.trace_operation(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__qualname__}"
            with tracing_manager.trace_operation(name):
                return func(*args, **kwargs)

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
