"""
Agent审批实体

管理Agent版本的审批流程，支持多级审批链、批准、拒绝和升级操作。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import ApprovalStatus


@dataclass
class AgentApproval(BaseEntity):
    """Agent审批实体

    管理单次审批请求的完整生命周期。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        approval_status: 审批状态
        requested_by: 请求者标识
        reviewed_by: 审批者标识
        review_notes: 审批意见
        requested_at: 请求时间
        reviewed_at: 审批时间
        approval_chain: 审批链记录
    """

    agent_id: str = ""
    version_id: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: Optional[str] = field(default=None)
    reviewed_by: Optional[str] = field(default=None)
    review_notes: Optional[str] = field(default=None)
    requested_at: Optional[datetime] = field(default=None)
    reviewed_at: Optional[datetime] = field(default=None)
    approval_chain: list[dict[str, Any]] = field(default_factory=list)

    def _append_chain_record(
        self,
        action: str,
        reviewer: str,
        notes: str = "",
    ) -> None:
        """追加审批链记录

        Args:
            action: 操作类型
            reviewer: 审批者
            notes: 备注
        """
        self.approval_chain.append({
            "action": action,
            "reviewer": reviewer,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def approve(
        self,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """批准审批请求

        Args:
            reviewer: 审批者标识
            notes: 审批意见
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许批准
        """
        if self.approval_status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            raise BusinessRuleViolationException(
                rule="APPROVAL_STATUS",
                message=f"审批当前状态为 {self.approval_status.value}，无法批准",
            )
        self.approval_status = ApprovalStatus.APPROVED
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = datetime.now(timezone.utc)
        self._append_chain_record("approve", reviewer, notes)
        self.touch(operator)

    def reject(
        self,
        reviewer: str,
        reason: str,
        operator: Optional[str] = None,
    ) -> None:
        """拒绝审批请求

        Args:
            reviewer: 审批者标识
            reason: 拒绝原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许拒绝
        """
        if self.approval_status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            raise BusinessRuleViolationException(
                rule="APPROVAL_STATUS",
                message=f"审批当前状态为 {self.approval_status.value}，无法拒绝",
            )
        self.approval_status = ApprovalStatus.REJECTED
        self.reviewed_by = reviewer
        self.review_notes = reason
        self.reviewed_at = datetime.now(timezone.utc)
        self._append_chain_record("reject", reviewer, reason)
        self.touch(operator)

    def escalate(
        self,
        reviewer: str,
        reason: str,
        operator: Optional[str] = None,
    ) -> None:
        """升级审批请求

        将审批请求升级到更高层级的审批者。

        Args:
            reviewer: 升级操作者标识
            reason: 升级原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审批状态不允许升级
        """
        if self.approval_status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            raise BusinessRuleViolationException(
                rule="APPROVAL_STATUS",
                message=f"审批当前状态为 {self.approval_status.value}，无法升级",
            )
        self.approval_status = ApprovalStatus.ESCALATED
        self._append_chain_record("escalate", reviewer, reason)
        self.touch(operator)
