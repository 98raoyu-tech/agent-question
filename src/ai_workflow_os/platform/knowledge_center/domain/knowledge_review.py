"""
知识审核实体

定义知识版本的审核流程实体，支持审核的提交、批准和驳回。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ReviewStatus(str, Enum):
    """审核状态枚举"""

    PENDING = "pending"
    """待审核"""

    APPROVED = "approved"
    """已通过"""

    REJECTED = "rejected"
    """已驳回"""

    REQUESTED_CHANGES = "requested_changes"
    """要求修改"""


@dataclass
class KnowledgeReview(BaseEntity):
    """知识审核实体

    记录知识版本的审核过程，包含审核意见和质量评分。

    Attributes:
        knowledge_source_id: 所属知识源标识
        version_id: 关联版本标识
        reviewer_id: 审核人标识
        status: 审核状态
        review_notes: 审核意见
        reviewed_at: 审核时间
        review_criteria: 审核标准
        quality_score: 质量评分
    """

    knowledge_source_id: str = ""
    version_id: str = ""
    reviewer_id: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    review_notes: str = ""
    reviewed_at: Optional[datetime] = None
    review_criteria: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0

    def approve(
        self,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> None:
        """通过审核

        仅待审核状态可执行通过操作。

        Args:
            reviewer: 审核人标识
            notes: 审核意见
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审核状态不允许通过
        """
        if self.status != ReviewStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="REVIEW_APPROVE_TRANSITION",
                message=f"当前审核状态 [{self.status.value}] 不允许通过，仅 PENDING 状态可操作",
            )
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
        """驳回审核

        仅待审核状态可执行驳回操作。

        Args:
            reviewer: 审核人标识
            reason: 驳回原因
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审核状态不允许驳回
        """
        if self.status != ReviewStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="REVIEW_REJECT_TRANSITION",
                message=f"当前审核状态 [{self.status.value}] 不允许驳回，仅 PENDING 状态可操作",
            )
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

        仅待审核状态可执行要求修改操作。

        Args:
            reviewer: 审核人标识
            notes: 修改意见
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 审核状态不允许要求修改
        """
        if self.status != ReviewStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="REVIEW_REQUEST_CHANGES_TRANSITION",
                message=f"当前审核状态 [{self.status.value}] 不允许要求修改，仅 PENDING 状态可操作",
            )
        self.status = ReviewStatus.REQUESTED_CHANGES
        self.reviewer_id = reviewer
        self.review_notes = notes
        self.reviewed_at = datetime.now(timezone.utc)
        self.touch(operator)
