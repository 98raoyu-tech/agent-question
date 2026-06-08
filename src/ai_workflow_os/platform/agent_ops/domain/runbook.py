"""
运维手册实体

定义Agent运维手册的核心业务实体，包含手册内容、执行记录和步骤管理。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class RunbookStep:
    """运维手册步骤值对象

    Attributes:
        step_id: 步骤标识
        title: 步骤标题
        description: 步骤描述
        action_type: 操作类型（manual/automated）
        command: 执行命令（自动化步骤）
        expected_result: 预期结果
        order: 执行顺序
    """

    step_id: str = ""
    title: str = ""
    description: str = ""
    action_type: str = "manual"
    command: Optional[str] = None
    expected_result: Optional[str] = None
    order: int = 0


@dataclass
class RunbookExecution:
    """运维手册执行记录值对象

    Attributes:
        execution_id: 执行标识
        executed_at: 执行时间
        executed_by: 执行者
        context: 执行上下文
        status: 执行状态
        result: 执行结果
    """

    execution_id: str = ""
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_by: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "completed"
    result: Optional[str] = None


@dataclass
class Runbook(BaseEntity):
    """运维手册实体

    定义Agent的运维手册，包含操作步骤、触发条件和执行历史。

    Attributes:
        name: 手册名称
        description: 手册描述
        agent_id: Agent标识
        trigger_condition: 触发条件描述
        steps: 操作步骤列表
        is_active: 是否激活
        last_executed_at: 最后执行时间
        execution_count: 执行次数
    """

    name: str = ""
    description: str = ""
    agent_id: str = ""
    trigger_condition: str = ""
    steps: list[RunbookStep] = field(default_factory=list)
    is_active: bool = True
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0

    def activate(self, operator: Optional[str] = None) -> None:
        """激活运维手册

        Args:
            operator: 操作者标识
        """
        self.is_active = True
        self.touch(operator)

    def deactivate(self, operator: Optional[str] = None) -> None:
        """停用运维手册

        Args:
            operator: 操作者标识
        """
        self.is_active = False
        self.touch(operator)

    def execute(self, context: dict[str, Any], operator: Optional[str] = None) -> RunbookExecution:
        """执行运维手册

        Args:
            context: 执行上下文
            operator: 操作者标识

        Returns:
            执行记录

        Raises:
            ValueError: 手册未激活或没有步骤
        """
        if not self.is_active:
            raise ValueError("未激活的运维手册不能执行")

        if not self.steps:
            raise ValueError("运维手册没有定义步骤")

        # 更新执行统计
        self.execution_count += 1
        self.last_executed_at = datetime.now(timezone.utc)
        self.touch(operator)

        # 创建执行记录
        execution = RunbookExecution(
            execution_id=f"{self.id}_{self.execution_count}",
            executed_by=operator,
            context=context,
            status="completed",
        )

        return execution

    def add_step(self, step: RunbookStep, operator: Optional[str] = None) -> None:
        """添加步骤

        Args:
            step: 手册步骤
            operator: 操作者标识
        """
        # 设置步骤顺序
        step.order = len(self.steps) + 1
        if not step.step_id:
            step.step_id = f"step_{step.order}"

        self.steps.append(step)
        self.touch(operator)

    def remove_step(self, step_id: str, operator: Optional[str] = None) -> None:
        """移除步骤

        Args:
            step_id: 步骤标识
            operator: 操作者标识
        """
        self.steps = [s for s in self.steps if s.step_id != step_id]
        # 重新排序
        for idx, step in enumerate(self.steps, start=1):
            step.order = idx
        self.touch(operator)

    def reorder_steps(self, step_ids: list[str], operator: Optional[str] = None) -> None:
        """重新排序步骤

        Args:
            step_ids: 步骤标识列表（按新顺序）
            operator: 操作者标识
        """
        step_map = {s.step_id: s for s in self.steps}
        reordered_steps: list[RunbookStep] = []

        for idx, step_id in enumerate(step_ids, start=1):
            if step_id in step_map:
                step = step_map[step_id]
                step.order = idx
                reordered_steps.append(step)

        self.steps = reordered_steps
        self.touch(operator)
