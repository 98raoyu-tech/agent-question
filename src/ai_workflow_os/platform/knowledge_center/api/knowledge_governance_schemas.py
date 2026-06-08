"""
知识治理请求/响应Schema

定义知识治理相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.knowledge_approval import ApprovalStatus
from ..domain.knowledge_lineage import KnowledgeLineage
from ..domain.knowledge_publish_record import PublishStatus
from ..domain.knowledge_review import ReviewStatus
from ..domain.knowledge_version import VersionStatus


# =============================================================================
# 版本Schema
# =============================================================================


class CreateVersionRequest(CreateDTO):
    """创建版本请求"""

    source_id: str = Field(description="知识源标识")
    change_log: str = Field(default="", max_length=5000, description="变更日志")
    snapshot: dict[str, Any] = Field(default_factory=dict, description="版本快照数据")


class VersionResponse(BaseDTO):
    """版本响应"""

    knowledge_source_id: str = Field(description="所属知识源标识")
    version_number: int = Field(description="版本号")
    change_log: str = Field(description="变更日志")
    snapshot: dict[str, Any] = Field(description="版本快照数据")
    is_current: bool = Field(description="是否为当前版本")
    status: VersionStatus = Field(description="版本状态")


class VersionListResponse(BaseModel):
    """版本列表响应"""

    items: list[VersionResponse] = Field(description="版本列表")
    total: int = Field(description="总数")


# =============================================================================
# 审核Schema
# =============================================================================


class SubmitReviewRequest(CreateDTO):
    """提交审核请求"""

    version_id: str = Field(description="版本标识")
    reviewer_id: str = Field(default="", description="审核人标识")


class ReviewActionRequest(BaseModel):
    """审核操作请求"""

    reviewer: str = Field(description="审核人标识")
    notes: str = Field(default="", max_length=5000, description="审核意见")


class ReviewResponse(BaseDTO):
    """审核响应"""

    knowledge_source_id: str = Field(description="所属知识源标识")
    version_id: str = Field(description="关联版本标识")
    reviewer_id: str = Field(description="审核人标识")
    status: ReviewStatus = Field(description="审核状态")
    review_notes: str = Field(description="审核意见")
    reviewed_at: Optional[datetime] = Field(default=None, description="审核时间")
    review_criteria: dict[str, Any] = Field(description="审核标准")
    quality_score: float = Field(description="质量评分")


class ReviewListResponse(BaseModel):
    """审核列表响应"""

    items: list[ReviewResponse] = Field(description="审核列表")
    total: int = Field(description="总数")


# =============================================================================
# 审批Schema
# =============================================================================


class SubmitApprovalRequest(CreateDTO):
    """提交审批请求"""

    version_id: str = Field(description="版本标识")
    requester: str = Field(default="", description="发起人标识")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    approver: str = Field(description="审批人标识")
    notes: str = Field(default="", max_length=5000, description="审批意见")


class ApprovalResponse(BaseDTO):
    """审批响应"""

    knowledge_source_id: str = Field(description="所属知识源标识")
    version_id: str = Field(description="关联版本标识")
    requested_by: str = Field(description="发起人标识")
    approved_by: Optional[str] = Field(default=None, description="审批人标识")
    status: ApprovalStatus = Field(description="审批状态")
    requested_at: datetime = Field(description="发起时间")
    approved_at: Optional[datetime] = Field(default=None, description="审批时间")
    approval_chain: list[dict[str, Any]] = Field(description="审批链记录")
    rejection_reason: Optional[str] = Field(default=None, description="驳回原因")


class ApprovalListResponse(BaseModel):
    """审批列表响应"""

    items: list[ApprovalResponse] = Field(description="审批列表")
    total: int = Field(description="总数")


# =============================================================================
# 发布Schema
# =============================================================================


class PublishVersionRequest(CreateDTO):
    """发布版本请求"""

    version_id: str = Field(description="版本标识")
    environment: str = Field(default="production", description="发布环境")


class RollbackPublishRequest(BaseModel):
    """回滚发布请求"""

    target_version_id: str = Field(description="回滚目标版本标识")


class PublishRecordResponse(BaseDTO):
    """发布记录响应"""

    knowledge_source_id: str = Field(description="所属知识源标识")
    version_id: str = Field(description="关联版本标识")
    published_by: str = Field(description="发布人标识")
    published_at: datetime = Field(description="发布时间")
    environment: str = Field(description="发布环境")
    status: PublishStatus = Field(description="发布状态")
    rollback_version_id: Optional[str] = Field(default=None, description="回滚目标版本标识")


class PublishHistoryResponse(BaseModel):
    """发布历史响应"""

    items: list[PublishRecordResponse] = Field(description="发布记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 血缘Schema
# =============================================================================


class LineageResponse(BaseDTO):
    """血缘响应"""

    source_id: str = Field(description="所属知识源标识")
    parent_version_id: str = Field(description="父版本标识")
    child_version_id: str = Field(description="子版本标识")
    transformation_type: str = Field(description="转换类型")
    transformation_details: dict[str, Any] = Field(description="转换详情")


class LineageListResponse(BaseModel):
    """血缘列表响应"""

    items: list[LineageResponse] = Field(description="血缘关系列表")
    total: int = Field(description="总数")
