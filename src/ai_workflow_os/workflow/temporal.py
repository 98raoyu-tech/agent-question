"""
Temporal 集成

提供基于 Temporal 的持久化工作流引擎实现。
"""

import asyncio
from typing import Any, Optional

from .engine import (
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowExecution,
    WorkflowStatus,
)


class TemporalWorkflowEngine(WorkflowEngine):
    """基于 Temporal 的工作流引擎

    继承自 WorkflowEngine，集成 Temporal 持久化能力。

    Attributes:
        temporal_client: Temporal 客户端连接
        task_queue: Temporal 任务队列名称
    """

    def __init__(self, task_queue: str = "ai-workflow-queue") -> None:
        """初始化 Temporal 工作流引擎

        Args:
            task_queue: Temporal 任务队列名称
        """
        super().__init__()
        self.temporal_client: Any = None
        self.task_queue: str = task_queue

    async def connect(
        self,
        host: str = "localhost",
        port: int = 7233,
    ) -> None:
        """连接到 Temporal 服务

        Args:
            host: Temporal 服务地址
            port: Temporal 服务端口

        Raises:
            ConnectionError: 连接失败
        """
        try:
            # 尝试导入 Temporal SDK
            from temporalio.client import Client

            self.temporal_client = await Client.connect(
                f"{host}:{port}",
                namespace="default",
            )
        except ImportError:
            # 如果未安装 Temporal SDK，使用模拟客户端
            self.temporal_client = _MockTemporalClient()
        except Exception as e:
            raise ConnectionError(f"连接 Temporal 服务失败: {e}")

    async def start_workflow_execution(
        self,
        definition: WorkflowDefinition,
        input_data: dict[str, Any],
        workflow_id: Optional[str] = None,
    ) -> WorkflowExecution:
        """使用 Temporal 启动工作流

        Args:
            definition: 工作流定义
            input_data: 输入数据
            workflow_id: 可选的工作流ID，用于幂等性

        Returns:
            工作流执行实例

        Raises:
            RuntimeError: Temporal 客户端未连接
        """
        if self.temporal_client is None:
            raise RuntimeError("Temporal 客户端未连接，请先调用 connect() 方法")

        # 注册工作流定义
        self.register_workflow(definition)

        # 启动 Temporal 工作流
        try:
            # 使用 Temporal SDK 启动工作流
            handle = await self.temporal_client.start_workflow(
                "WorkflowExecution",
                input_data,
                id=workflow_id or f"wf-{definition.workflow_id}",
                task_queue=self.task_queue,
            )

            # 创建执行实例
            execution = WorkflowExecution(
                workflow_id=definition.workflow_id,
                status=WorkflowStatus.RUNNING,
                input_data=input_data,
            )

            # 保存执行句柄以便后续操作
            execution.context = {"temporal_handle": handle}
            self.executions[execution.execution_id] = execution

            return execution

        except Exception as e:
            raise RuntimeError(f"启动 Temporal 工作流失败: {e}")

    async def signal_workflow(
        self,
        execution_id: str,
        signal_name: str,
        payload: dict[str, Any],
    ) -> None:
        """向运行中的工作流发送信号

        Args:
            execution_id: 执行ID
            signal_name: 信号名称
            payload: 信号负载数据

        Raises:
            ValueError: 执行不存在
            RuntimeError: 无法发送信号
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        context = getattr(execution, "context", {})
        handle = context.get("temporal_handle")

        if handle is None:
            raise RuntimeError("执行实例缺少 Temporal 句柄")

        try:
            await handle.signal(signal_name, payload)
        except Exception as e:
            raise RuntimeError(f"发送信号失败: {e}")

    async def query_workflow(
        self,
        execution_id: str,
        query_name: str,
    ) -> dict[str, Any]:
        """查询工作流状态

        Args:
            execution_id: 执行ID
            query_name: 查询名称

        Returns:
            查询结果

        Raises:
            ValueError: 执行不存在
            RuntimeError: 查询失败
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        context = getattr(execution, "context", {})
        handle = context.get("temporal_handle")

        if handle is None:
            raise RuntimeError("执行实例缺少 Temporal 句柄")

        try:
            result = await handle.query(query_name)
            return result
        except Exception as e:
            raise RuntimeError(f"查询工作流失败: {e}")

    async def terminate_workflow(
        self,
        execution_id: str,
        reason: str = "",
    ) -> None:
        """终止工作流

        Args:
            execution_id: 执行ID
            reason: 终止原因

        Raises:
            ValueError: 执行不存在
            RuntimeError: 终止失败
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        context = getattr(execution, "context", {})
        handle = context.get("temporal_handle")

        if handle is None:
            raise RuntimeError("执行实例缺少 Temporal 句柄")

        try:
            await handle.terminate(reason=reason)
            execution.status = WorkflowStatus.FAILED
            execution.output_data["terminated_reason"] = reason
        except Exception as e:
            raise RuntimeError(f"终止工作流失败: {e}")


class _MockTemporalClient:
    """模拟 Temporal 客户端

    用于在未安装 Temporal SDK 时提供基本功能。
    """

    async def start_workflow(
        self,
        workflow_type: str,
        *args: Any,
        **kwargs: Any,
    ) -> "_MockWorkflowHandle":
        """模拟启动工作流"""
        return _MockWorkflowHandle()


class _MockWorkflowHandle:
    """模拟工作流句柄"""

    async def signal(self, signal_name: str, payload: Any) -> None:
        """模拟发送信号"""
        pass

    async def query(self, query_name: str) -> dict[str, Any]:
        """模拟查询"""
        return {"status": "mock"}

    async def terminate(self, reason: str = "") -> None:
        """模拟终止"""
        pass