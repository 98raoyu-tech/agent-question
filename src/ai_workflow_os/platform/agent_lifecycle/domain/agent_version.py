"""
Agent生命周期版本实体

管理Agent的版本历史，支持版本审批流程（批准/拒绝）。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import AgentLifecycleState, ApprovalStatus


@dataclass
class AgentLifecycleVersion(BaseEntity):
    """Agent生命周期版本实体

    记录Agent定义的版本快照，附带生命周期状态和审批状态。

    Attributes:
        agent_id: 关联的Agent标识
        version_number: 版本号
        change_log: 变更日志
        snapshot: Agent定义快照数据
        is_current: 是否为当前版本
        lifecycle_state: 版本的生命周期状态
        approval_status: 审批状态
        approved_by: 审批者标识
        approved_at: 审批时间
        rejection_reason: 拒绝原因
    """

    agent_id: str = ""
    version_number: str = ""
    change_log: str = ""
    snapshot: dict[str, Any] = field(default_factory=dict)
    is_current: bool = False
    lifecycle_state: AgentLifecycleState = AgentLifecycleState.DRAFT
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = field(default=None)
    approved_at: Optional[datetime] = field(default=None)
    rejection_reason: Optional[str] = field(default=None)

    def approve(self, operator: Optional[str] = None) -> None:
        """批准该版本

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许批准
        """
        if self.approval_status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            raise BusinessRuleViolationException(
                rule="VERSION_APPROVAL_STATUS",
                message=f"版本当前审批状态为 {self.approval_status.value}，无法批准",
            )
        self.approval_status = ApprovalStatus.APPROVED
        self.approved_by = operator
        self.approved_at = datetime.now(timezone.utc)
        self.touch(operator)

    def reject(self, reason: str, operator: Optional[str] = None) -> None:
        """拒绝该版本

        Args:
            reason: 拒绝原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许拒绝
        """
        if self.approval_status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            raise BusinessRuleViolationException(
                rule="VERSION_REJECTION_STATUS",
                message=f"版本当前审批状态为 {self.approval_status.value}，无法拒绝",
            )
        self.approval_status = ApprovalStatus.REJECTED
        self.rejection_reason = reason
        self.approved_by = operator
        self.approved_at = datetime.now(timezone.utc)
        self.touch(operator)

    def set_as_current(self, operator: Optional[str] = None) -> None:
        """设置为当前版本"""
        self.is_current = True
        self.touch(operator)

    def unset_current(self, operator: Optional[str] = None) -> None:
        """取消当前版本标记"""
        self.is_current = False
        self.touch(operator)
