"""
工具评审实体

管理工具发布前的评审流程。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ReviewStatus(str, Enum):
    """评审状态枚举"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUESTED_CHANGES = "requested_changes"


@dataclass
class ToolReview(BaseEntity):
    """工具评审实体

    记录工具的评审状态、评分和评审意见。

    Attributes:
        tool_id: 关联的工具标识
        reviewer_id: 评审人标识
        status: 评审状态
        review_notes: 评审备注
        reviewed_at: 评审完成时间
        criteria_scores: 各维度评分
        overall_score: 综合评分
    """

    tool_id: str = ""
    reviewer_id: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    review_notes: str = ""
    reviewed_at: Optional[datetime] = field(default=None)
    criteria_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0

    def approve(
        self,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """通过评审

        Args:
            reviewer: 评审人标识
            notes: 评审备注
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 评审状态不允许该操作
        """
        self._ensure_pending()
        self.status = ReviewStatus.APPROVED
        self.reviewer_id = reviewer
        self.review_notes = notes
        self.reviewed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def reject(
        self,
        reviewer: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """驳回评审

        Args:
            reviewer: 评审人标识
            reason: 驳回原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 评审状态不允许该操作
        """
        self._ensure_pending()
        self.status = ReviewStatus.REJECTED
        self.reviewer_id = reviewer
        self.review_notes = reason
        self.reviewed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def request_changes(
        self,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """要求修改

        Args:
            reviewer: 评审人标识
            notes: 修改意见
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 评审状态不允许该操作
        """
        self._ensure_pending()
        self.status = ReviewStatus.REQUESTED_CHANGES
        self.reviewer_id = reviewer
        self.review_notes = notes
        self.reviewed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def _ensure_pending(self) -> None:
        """校验评审状态为待处理"""
        if self.status != ReviewStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="REVIEW_STATUS_TRANSITION",
                message=f"评审 [{self.id}] 当前状态为 {self.status.value}，不允许该操作",
            )
