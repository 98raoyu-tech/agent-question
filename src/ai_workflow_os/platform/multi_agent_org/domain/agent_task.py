"""
Agent任务实体

定义多智能体协作任务的核心领域实体，管理任务的创建、分配、执行和完成生命周期。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import TaskStatus

NON_BLOCKING_STATES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


@dataclass
class AgentTask(BaseEntity):
    """Agent任务实体

    表示一个分配给Agent或团队的协作任务，支持子任务拆分和进度追踪。

    Attributes:
        title: 任务标题
        description: 任务描述
        assigned_agent_id: 分配的Agent标识
        team_id: 所属团队标识
        status: 任务状态
        priority: 优先级（1-10，数值越大优先级越高）
        context: 任务上下文
        result: 执行结果
        parent_task_id: 父任务标识
        sub_task_ids: 子任务标识列表
        deadline: 截止时间
        started_at: 开始时间
        completed_at: 完成时间
        error_message: 错误信息
    """

    title: str = ""
    description: str = ""
    assigned_agent_id: Optional[str] = field(default=None)
    team_id: Optional[str] = field(default=None)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    context: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    parent_task_id: Optional[str] = field(default=None)
    sub_task_ids: list[str] = field(default_factory=list)
    deadline: Optional[datetime] = field(default=None)
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    error_message: Optional[str] = field(default=None)

    def assign(self, agent_id: str, operator: Optional[str] = None) -> None:
        """分配任务给Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务状态不允许分配
        """
        if self.status not in {TaskStatus.PENDING}:
            raise BusinessRuleViolationException(
                rule="TASK_STATUS_TRANSITION",
                message=f"任务 [{self.id}] 当前状态为 {self.status.value}，无法分配",
            )
        self.assigned_agent_id = agent_id
        self.status = TaskStatus.ASSIGNED
        self.touch(operator)

    def start(self, operator: Optional[str] = None) -> None:
        """开始执行任务

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务状态不允许开始执行
        """
        if self.status not in {TaskStatus.ASSIGNED, TaskStatus.PENDING}:
            raise BusinessRuleViolationException(
                rule="TASK_STATUS_TRANSITION",
                message=f"任务 [{self.id}] 当前状态为 {self.status.value}，无法开始执行",
            )
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
        self.touch(operator)

    def complete(self, result: dict[str, Any], operator: Optional[str] = None) -> None:
        """完成任务

        Args:
            result: 执行结果
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务状态不允许完成
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="TASK_STATUS_TRANSITION",
                message=f"任务 [{self.id}] 当前状态为 {self.status.value}，无法完成",
            )
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail(self, error: str, operator: Optional[str] = None) -> None:
        """标记任务失败

        Args:
            error: 错误描述
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务状态不允许标记失败
        """
        if self.status not in {TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS}:
            raise BusinessRuleViolationException(
                rule="TASK_STATUS_TRANSITION",
                message=f"任务 [{self.id}] 当前状态为 {self.status.value}，无法标记失败",
            )
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def cancel(self, operator: Optional[str] = None) -> None:
        """取消任务

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务状态不允许取消
        """
        if self.status in NON_BLOCKING_STATES:
            raise BusinessRuleViolationException(
                rule="TASK_STATUS_TRANSITION",
                message=f"任务 [{self.id}] 当前状态为 {self.status.value}，无法取消",
            )
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def add_sub_task(self, task_id: str, operator: Optional[str] = None) -> None:
        """添加子任务

        Args:
            task_id: 子任务标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 任务已终止
        """
        if self.status in NON_BLOCKING_STATES:
            raise BusinessRuleViolationException(
                rule="TASK_ALREADY_TERMINATED",
                message=f"任务 [{self.id}] 已终止，无法添加子任务",
            )
        if task_id not in self.sub_task_ids:
            self.sub_task_ids.append(task_id)
            self.touch(operator)

    def is_overdue(self) -> bool:
        """判断任务是否已逾期

        Returns:
            任务未完成且超过截止时间返回True
        """
        if self.status in NON_BLOCKING_STATES or self.deadline is None:
            return False
        return datetime.now(timezone.utc) > self.deadline
