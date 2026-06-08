"""
Agent委托实体

定义Agent间任务委托的核心领域实体，管理委托的创建、接受、拒绝、执行和完成生命周期。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import TaskStatus


@dataclass
class AgentDelegation(BaseEntity):
    """Agent委托实体

    表示一个Agent向另一个Agent委托任务的完整生命周期。

    Attributes:
        delegator_agent_id: 委托方Agent标识
        delegate_agent_id: 被委托方Agent标识
        task_description: 任务描述
        task_context: 任务上下文
        status: 委托状态
        delegated_at: 委托时间
        accepted_at: 接受时间
        completed_at: 完成时间
        result: 执行结果
        error_message: 错误信息
        priority: 优先级（1-10）
    """

    delegator_agent_id: str = ""
    delegate_agent_id: str = ""
    task_description: str = ""
    task_context: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    delegated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    result: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = field(default=None)
    priority: int = 5

    def accept(self, operator: Optional[str] = None) -> None:
        """接受委托

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许接受
        """
        if self.status != TaskStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法接受",
            )
        self.status = TaskStatus.ASSIGNED
        self.accepted_at = datetime.now(timezone.utc)
        self.touch(operator)

    def reject(self, reason: str, operator: Optional[str] = None) -> None:
        """拒绝委托

        Args:
            reason: 拒绝原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许拒绝
        """
        if self.status != TaskStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法拒绝",
            )
        self.status = TaskStatus.CANCELLED
        self.error_message = reason
        self.touch(operator)

    def start(self, operator: Optional[str] = None) -> None:
        """开始执行委托任务

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许开始执行
        """
        if self.status != TaskStatus.ASSIGNED:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法开始执行",
            )
        self.status = TaskStatus.IN_PROGRESS
        self.touch(operator)

    def complete(self, result: dict[str, Any], operator: Optional[str] = None) -> None:
        """完成委托任务

        Args:
            result: 执行结果
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许完成
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法完成",
            )
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail(self, error: str, operator: Optional[str] = None) -> None:
        """标记委托任务失败

        Args:
            error: 错误描述
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许标记失败
        """
        if self.status not in {TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS}:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法标记失败",
            )
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def cancel(self, operator: Optional[str] = None) -> None:
        """取消委托任务

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 委托状态不允许取消
        """
        terminal_states = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        if self.status in terminal_states:
            raise BusinessRuleViolationException(
                rule="DELEGATION_STATUS_TRANSITION",
                message=f"委托 [{self.id}] 当前状态为 {self.status.value}，无法取消",
            )
        self.status = TaskStatus.CANCELLED
        self.touch(operator)
