"""
知识审批实体

定义知识版本的审批流程实体，支持多级审批链。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ApprovalStatus(str, Enum):
    """审批状态枚举"""

    PENDING = "pending"
    """待审批"""

    APPROVED = "approved"
    """已批准"""

    REJECTED = "rejected"
    """已驳回"""

    ESCALATED = "escalated"
    """已升级"""


@dataclass
class KnowledgeApproval(BaseEntity):
    """知识审批实体

    记录知识版本的审批过程，支持多级审批链和审批升级。

    Attributes:
        knowledge_source_id: 所属知识源标识
        version_id: 关联版本标识
        requested_by: 发起人标识
        approved_by: 审批人标识
        status: 审批状态
        requested_at: 发起时间
        approved_at: 审批时间
        approval_chain: 审批链记录
        rejection_reason: 驳回原因
    """

    knowledge_source_id: str = ""
    version_id: str = ""
    requested_by: str = ""
    approved_by: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approval_chain: list[dict[str, Any]] = field(default_factory=list)
    rejection_reason: Optional[str] = None

    def approve(
        self,
        approver: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """批准审批

        仅待审批状态可执行批准操作，审批通过后记录审批链。

        Args:
            approver: 审批人标识
            notes: 审批意见
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许批准
        """
        if self.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="APPROVAL_APPROVE_TRANSITION",
                message=f"当前审批状态 [{self.status.value}] 不允许批准，仅 PENDING 状态可操作",
            )
        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.approved_at = datetime.now(timezone.utc)
        self.approval_chain.append({
            "action": "approve",
            "approver": approver,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.touch(operator)

    def reject(
        self,
        approver: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """驳回审批

        仅待审批状态可执行驳回操作。

        Args:
            approver: 审批人标识
            reason: 驳回原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许驳回
        """
        if self.status != ApprovalStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="APPROVAL_REJECT_TRANSITION",
                message=f"当前审批状态 [{self.status.value}] 不允许驳回，仅 PENDING 状态可操作",
            )
        self.status = ApprovalStatus.REJECTED
        self.approved_by = approver
        self.approved_at = datetime.now(timezone.utc)
        self.rejection_reason = reason
        self.approval_chain.append({
            "action": "reject",
            "approver": approver,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.touch(operator)
