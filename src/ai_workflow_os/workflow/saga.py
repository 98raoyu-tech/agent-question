"""
Saga 模式实现

提供分布式 Saga 模式，支持跨服务回滚。
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional


# ==================== 枚举定义 ====================

class SagaStatus(str, Enum):
    """Saga 执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


# ==================== 数据类定义 ====================

@dataclass
class SagaStep:
    """Saga 步骤定义

    Attributes:
        step_id: 步骤唯一标识
        action: 步骤执行动作（异步函数）
        compensation: 补偿动作（异步函数）
        completed: 是否已完成
        result: 执行结果
        error: 错误信息
    """
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    action: Callable[..., Coroutine[Any, Any, Any]] = None
    compensation: Callable[..., Coroutine[Any, Any, Any]] = None
    completed: bool = False
    result: Any = None
    error: Optional[str] = None


@dataclass
class SagaExecution:
    """Saga 执行实例

    Attributes:
        saga_id: Saga 唯一标识
        steps: 步骤列表
        completed_steps: 已完成的步骤ID列表
        status: 执行状态
        started_at: 开始时间
        completed_at: 完成时间
        context: 执行上下文
        error: 错误信息
    """
    saga_id: str = field(default_factory=lambda: f"saga_{uuid.uuid4().hex[:12]}")
    steps: list[SagaStep] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    status: SagaStatus = SagaStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


# ==================== Saga 编排器 ====================

class SagaOrchestrator:
    """Saga 编排器

    实现分布式 Saga 模式，支持跨服务回滚。

    Attributes:
        steps: 步骤列表
        execution: 当前执行实例
    """

    def __init__(self) -> None:
        """初始化 Saga 编排器"""
        self.steps: list[SagaStep] = []
        self.execution: Optional[SagaExecution] = None

    def add_step(
        self,
        step_id: str,
        action: Callable[..., Coroutine[Any, Any, Any]],
        compensation: Callable[..., Coroutine[Any, Any, Any]],
    ) -> None:
        """添加 Saga 步骤

        Args:
            step_id: 步骤ID
            action: 执行动作
            compensation: 补偿动作
        """
        step = SagaStep(
            step_id=step_id,
            action=action,
            compensation=compensation,
        )
        self.steps.append(step)

    async def execute(
        self,
        context: dict[str, Any],
    ) -> SagaExecution:
        """执行 Saga

        Args:
            context: 执行上下文

        Returns:
            Saga 执行实例
        """
        # 创建执行实例
        self.execution = SagaExecution(
            steps=self.steps.copy(),
            status=SagaStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            context=context,
        )

        try:
            # 按顺序执行每个步骤
            for step in self.execution.steps:
                await self._execute_step(step, context)
                self.execution.completed_steps.append(step.step_id)

            # 所有步骤执行成功
            self.execution.status = SagaStatus.COMPLETED
            self.execution.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            # 执行失败，开始补偿
            self.execution.error = str(e)
            self.execution.status = SagaStatus.FAILED
            self.execution.completed_at = datetime.now(timezone.utc)

            # 从失败步骤开始逆向补偿
            await self.compensate(step.step_id)

        return self.execution

    async def compensate(
        self,
        failed_step_id: str,
    ) -> None:
        """从失败步骤开始逆向补偿

        Args:
            failed_step_id: 失败的步骤ID
        """
        if self.execution is None:
            raise RuntimeError("没有正在执行的 Saga")

        self.execution.status = SagaStatus.COMPENSATING

        # 找到失败步骤的索引
        failed_index = -1
        for i, step in enumerate(self.execution.steps):
            if step.step_id == failed_step_id:
                failed_index = i
                break

        if failed_index == -1:
            raise ValueError(f"步骤不存在: {failed_step_id}")

        # 逆向执行补偿操作
        for i in range(failed_index, -1, -1):
            step = self.execution.steps[i]
            if step.completed:
                await self._execute_compensation(step, self.execution.context)

        self.execution.status = SagaStatus.COMPENSATED

    async def compensate_all(self) -> None:
        """补偿所有已完成步骤"""
        if self.execution is None:
            raise RuntimeError("没有正在执行的 Saga")

        self.execution.status = SagaStatus.COMPENSATING

        # 逆向补偿所有已完成步骤
        for step in reversed(self.execution.steps):
            if step.completed:
                await self._execute_compensation(step, self.execution.context)

        self.execution.status = SagaStatus.COMPENSATED

    async def _execute_step(
        self,
        step: SagaStep,
        context: dict[str, Any],
    ) -> Any:
        """执行单个步骤

        Args:
            step: 步骤定义
            context: 执行上下文

        Returns:
            步骤执行结果

        Raises:
            Exception: 步骤执行失败
        """
        try:
            # 执行步骤动作
            if step.action is None:
                raise ValueError(f"步骤 {step.step_id} 未定义执行动作")

            result = await step.action(context)
            step.completed = True
            step.result = result
            return result

        except Exception as e:
            step.error = str(e)
            raise

    async def _execute_compensation(
        self,
        step: SagaStep,
        context: dict[str, Any],
    ) -> None:
        """执行补偿操作

        Args:
            step: 步骤定义
            context: 执行上下文
        """
        try:
            if step.compensation is not None:
                await step.compensation(context)
        except Exception as e:
            # 补偿操作失败，记录错误但继续执行其他补偿
            step.error = f"补偿失败: {e}"