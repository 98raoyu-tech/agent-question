"""
Executor Agent - 任务执行智能体

负责按照执行计划逐步执行子任务，调用工具并处理执行结果。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import AgentResult, AgentStatus, AgentTask, AgentType, BaseAgent
from .planner import ExecutionPlan, SubTask


# ==================== 枚举定义 ====================

class RecoveryAction(str, Enum):
    """恢复动作枚举"""
    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"


# ==================== 数据类定义 ====================

@dataclass
class SubTaskResult:
    """子任务执行结果

    Attributes:
        task_id: 子任务 ID
        status: 执行状态
        output: 输出结果
        error: 错误信息
        duration_ms: 执行耗时（毫秒）
        tokens_used: 使用的 token 数量
    """
    task_id: str = ""
    status: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    tokens_used: int = 0


# ==================== Executor Agent ====================

class ExecutorAgent(BaseAgent):
    """任务执行智能体

    按照执行计划逐步执行子任务，支持工具调用和失败恢复。

    Attributes:
        tool_registry: 工具注册表
        memory: 记忆存储
        current_plan: 当前执行计划
        progress: 任务进度（0.0 - 1.0）
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "ExecutorAgent",
        tool_registry: Any = None,
        memory: Any = None,
    ) -> None:
        """初始化 Executor Agent

        Args:
            agent_id: Agent 唯一标识
            agent_name: Agent 名称
            tool_registry: 工具注册表实例
            memory: 记忆存储实例
        """
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=AgentType.EXECUTOR,
        )
        self.tool_registry = tool_registry
        self.memory = memory
        self.current_plan: ExecutionPlan | None = None
        self.progress: float = 0.0

    # ==================== 核心方法 ====================

    async def execute(self, task: AgentTask) -> AgentResult:
        """按照执行计划逐步执行子任务

        Args:
            task: 包含执行计划的任务

        Returns:
            执行结果
        """
        self.status = AgentStatus.RUNNING
        start_time = self._get_current_timestamp()

        try:
            # 提取执行计划
            plan_data = task.payload.get("execution_plan")
            if not plan_data:
                raise ValueError("任务负载中缺少执行计划")

            # 解析子任务列表
            sub_tasks = [
                SubTask(
                    task_id=st["task_id"],
                    description=st["description"],
                    dependencies=st.get("dependencies", []),
                    estimated_duration=st.get("estimated_duration", 0),
                    required_tools=st.get("required_tools", []),
                )
                for st in plan_data.get("sub_tasks", [])
            ]

            # 逐步执行子任务
            sub_task_results: list[SubTaskResult] = []
            for index, sub_task in enumerate(sub_tasks):
                # 更新进度
                self._update_progress(task.task_id, index / len(sub_tasks))

                # 执行子任务
                result = await self._execute_sub_task(sub_task)
                sub_task_results.append(result)

                # 检查是否执行失败
                if result.status == AgentStatus.FAILED.value:
                    recovery_action = await self._handle_failure(sub_task, result.error)

                    # 根据恢复策略处理
                    if recovery_action == RecoveryAction.RETRY:
                        result = await self._execute_sub_task(sub_task)
                        sub_task_results[-1] = result
                    elif recovery_action == RecoveryAction.SKIP:
                        continue
                    elif recovery_action == RecoveryAction.ROLLBACK:
                        raise RuntimeError(f"子任务 {sub_task.task_id} 执行失败，触发回滚")
                    elif recovery_action == RecoveryAction.ESCALATE:
                        raise RuntimeError(f"子任务 {sub_task.task_id} 执行失败，需要人工介入")

            # 更新进度为完成
            self._update_progress(task.task_id, 1.0)

            # 构建输出结果
            output = {
                "sub_task_results": [
                    {
                        "task_id": r.task_id,
                        "status": r.status,
                        "output": r.output,
                        "error": r.error,
                        "duration_ms": r.duration_ms,
                        "tokens_used": r.tokens_used,
                    }
                    for r in sub_task_results
                ],
                "total_tokens_used": sum(r.tokens_used for r in sub_task_results),
            }

            duration_ms = self._get_current_timestamp() - start_time
            self.status = AgentStatus.COMPLETED

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED.value,
                output=output,
                duration_ms=duration_ms,
                tokens_used=output["total_tokens_used"],
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            duration_ms = self._get_current_timestamp() - start_time

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.FAILED.value,
                error=str(e),
                duration_ms=duration_ms,
            )

    # ==================== 内部方法 ====================

    async def _execute_sub_task(self, sub_task: SubTask) -> SubTaskResult:
        """执行单个子任务

        Args:
            sub_task: 待执行的子任务

        Returns:
            子任务执行结果
        """
        start_time = self._get_current_timestamp()

        try:
            # 调用所需工具
            tool_outputs: dict[str, Any] = {}
            for tool_name in sub_task.required_tools:
                tool_output = await self._invoke_tool(tool_name, {
                    "task_id": sub_task.task_id,
                    "description": sub_task.description,
                })
                tool_outputs[tool_name] = tool_output

            duration_ms = self._get_current_timestamp() - start_time

            return SubTaskResult(
                task_id=sub_task.task_id,
                status=AgentStatus.COMPLETED.value,
                output={"tool_outputs": tool_outputs},
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = self._get_current_timestamp() - start_time

            return SubTaskResult(
                task_id=sub_task.task_id,
                status=AgentStatus.FAILED.value,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _invoke_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """调用指定工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具输出结果
        """
        # TODO: 集成实际的工具注册表
        if self.tool_registry:
            return await self.tool_registry.invoke(tool_name, params)

        # 模拟工具调用
        return {
            "tool": tool_name,
            "status": "success",
            "result": f"模拟 {tool_name} 执行结果",
        }

    async def _handle_failure(self, sub_task: SubTask, error: str) -> RecoveryAction:
        """处理执行失败，决定恢复策略

        Args:
            sub_task: 失败的子任务
            error: 错误信息

        Returns:
            恢复动作
        """
        # 简单的恢复策略：有依赖的任务失败时升级，无依赖的任务重试
        if sub_task.dependencies:
            return RecoveryAction.ESCALATE
        return RecoveryAction.RETRY

    def _update_progress(self, task_id: str, progress: float) -> None:
        """更新任务进度

        Args:
            task_id: 任务 ID
            progress: 进度值（0.0 - 1.0）
        """
        self.progress = max(0.0, min(1.0, progress))
        # TODO: 发送进度更新事件
        print(f"[Progress] Task {task_id}: {self.progress:.1%}")

    # ==================== 生命周期方法 ====================

    async def pause(self) -> None:
        """暂停 Executor Agent"""
        self.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """恢复 Executor Agent"""
        self.status = AgentStatus.RUNNING

    async def checkpoint(self) -> dict[str, Any]:
        """保存检查点

        Returns:
            检查点状态数据
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "progress": self.progress,
            "context": self.context,
        }

    async def restore(self, state: dict[str, Any]) -> None:
        """从检查点恢复状态

        Args:
            state: 检查点状态数据
        """
        self.agent_id = state.get("agent_id", self.agent_id)
        self.agent_name = state.get("agent_name", self.agent_name)
        self.status = AgentStatus(state.get("status", AgentStatus.IDLE.value))
        self.progress = state.get("progress", 0.0)
        self.context = state.get("context", {})

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_current_timestamp() -> float:
        """获取当前时间戳（毫秒）"""
        import time
        return time.time() * 1000