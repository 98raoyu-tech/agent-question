"""
工具审批实体

管理工具发布审批流程。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ApprovalStatus(str, Enum):
    """审批状态枚举"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ToolApproval(BaseEntity):
    """工具审批实体

    记录工具版本的审批流程状态。

    Attributes:
        tool_id: 关联的工具标识
        version_id: 关联的版本标识
        requested_by: 申请人标识
        approved_by: 审批人标识
        status: 审批状态
        requested_at: 申请时间
        approved_at: 审批完成时间
        approval_notes: 审批备注
        rejection_reason: 驳回原因
    """

    tool_id: str = ""
    version_id: str = ""
    requested_by: str = ""
    approved_by: Optional[str] = field(default=None)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: Optional[datetime] = field(default=None)
    approved_at: Optional[datetime] = field(default=None)
    approval_notes: str = ""
    rejection_reason: str = ""

    def approve(
        self,
        approver: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """批准工具

        Args:
            approver: 审批人标识
            notes: 审批备注
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许该操作
        """
        self._ensure_pending()
        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.approval_notes = notes
        self.approved_at = datetime.now(timezone.utc)
        self.touch(operator)

    def reject(
        self,
        approver: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """驳回工具

        Args:
            approver: 审批人标识
            reason: 驳回原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许该操作
        """
        self._ensure_pending()
        self.status = ApprovalStatus.REJECTED
        self.approved_by = approver
        self.rejection_reason = reason
        self.approved_at = datetime.now(timezone.utc)
        self.touch(operator)

    def _ensure_pending(self) -> None:
        """校验审批状态为待处理"""
        if self.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="APPROVAL_STATUS_TRANSITION",
                message=f"审批 [{self.id}] 当前状态为 {self.status.value}，不允许该操作",
            )
