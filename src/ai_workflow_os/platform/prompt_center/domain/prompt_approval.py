"""
Prompt审批实体

管理Prompt模板版本的审批流程。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ApprovalStatus(str, Enum):
    """审批状态枚举"""

    PENDING = "pending"
    """待审批"""

    APPROVED = "approved"
    """已批准"""

    REJECTED = "rejected"
    """已拒绝"""


@dataclass
class PromptApproval(BaseEntity):
    """Prompt审批实体

    管理Prompt模板版本的审批流程，支持批准和拒绝操作。

    Attributes:
        prompt_id: 关联的Prompt模板标识
        version_id: 关联的版本标识
        requested_by: 申请人标识
        approved_by: 审批人标识
        status: 审批状态
        requested_at: 申请时间
        approved_at: 审批时间
        approval_notes: 审批备注
        rejection_reason: 拒绝原因
        criteria: 审批标准
    """

    prompt_id: str = ""
    version_id: str = ""
    requested_by: str = ""
    approved_by: str | None = field(default=None)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime | None = field(default=None)
    approved_at: datetime | None = field(default=None)
    approval_notes: str | None = field(default=None)
    rejection_reason: str | None = field(default=None)
    criteria: dict[str, Any] = field(default_factory=dict)

    def approve(
        self,
        approver: str,
        notes: str | None = None,
        operator: str | None = None,
    ) -> None:
        """批准审批

        Args:
            approver: 审批人标识
            notes: 审批备注
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许批准
        """
        if self.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="approval_approve",
                message=f"审批当前状态为{self.status.value}，无法批准",
            )

        if not approver:
            raise BusinessRuleViolationException(
                rule="approval_approve",
                message="审批人标识不能为空",
            )

        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.approval_notes = notes
        self.approved_at = datetime.now(UTC)
        self.touch(operator)

    def reject(
        self,
        approver: str,
        reason: str,
        operator: str | None = None,
    ) -> None:
        """拒绝审批

        Args:
            approver: 审批人标识
            reason: 拒绝原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许拒绝
        """
        if self.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="approval_reject",
                message=f"审批当前状态为{self.status.value}，无法拒绝",
            )

        if not approver:
            raise BusinessRuleViolationException(
                rule="approval_reject",
                message="审批人标识不能为空",
            )

        if not reason or not reason.strip():
            raise BusinessRuleViolationException(
                rule="approval_reject",
                message="拒绝原因不能为空",
            )

        self.status = ApprovalStatus.REJECTED
        self.approved_by = approver
        self.rejection_reason = reason
        self.approved_at = datetime.now(UTC)
        self.touch(operator)
