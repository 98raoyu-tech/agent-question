"""
工具生命周期请求/响应Schema

定义评审、审批、安全扫描、使用分析和废弃相关的API数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.tool_approval import ApprovalStatus
from ..domain.tool_deprecation import DeprecationStatus
from ..domain.tool_review import ReviewStatus
from ..domain.tool_security_scan import ScanStatus, ScanType
from ..domain.tool_usage_analytics import ToolUsageAnalytics


# =============================================================================
# 评审Schema
# =============================================================================


class SubmitReviewRequest(CreateDTO):
    """提交评审请求"""

    tool_id: str = Field(min_length=1, description="工具标识")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class ReviewActionRequest(BaseModel):
    """评审操作请求"""

    reviewer: str = Field(min_length=1, description="评审人标识")
    notes: str = Field(default="", description="评审备注/原因")


class ReviewResponse(BaseDTO):
    """评审响应"""

    tool_id: str = Field(description="工具标识")
    reviewer_id: str = Field(description="评审人标识")
    status: ReviewStatus = Field(description="评审状态")
    review_notes: str = Field(description="评审备注")
    reviewed_at: Optional[datetime] = Field(default=None, description="评审完成时间")
    criteria_scores: dict[str, float] = Field(description="各维度评分")
    overall_score: float = Field(description="综合评分")


# =============================================================================
# 审批Schema
# =============================================================================


class SubmitApprovalRequest(CreateDTO):
    """提交审批请求"""

    tool_id: str = Field(min_length=1, description="工具标识")
    version_id: str = Field(min_length=1, description="版本标识")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    approver: str = Field(min_length=1, description="审批人标识")
    notes: str = Field(default="", description="审批备注/原因")


class ApprovalResponse(BaseDTO):
    """审批响应"""

    tool_id: str = Field(description="工具标识")
    version_id: str = Field(description="版本标识")
    requested_by: str = Field(description="申请人标识")
    approved_by: Optional[str] = Field(default=None, description="审批人标识")
    status: ApprovalStatus = Field(description="审批状态")
    requested_at: Optional[datetime] = Field(default=None, description="申请时间")
    approved_at: Optional[datetime] = Field(default=None, description="审批完成时间")
    approval_notes: str = Field(description="审批备注")
    rejection_reason: str = Field(description="驳回原因")


# =============================================================================
# 安全扫描Schema
# =============================================================================


class RunSecurityScanRequest(CreateDTO):
    """启动安全扫描请求"""

    tool_id: str = Field(min_length=1, description="工具标识")
    version_id: str = Field(min_length=1, description="版本标识")
    scan_type: ScanType = Field(description="扫描类型")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class SecurityScanResponse(BaseDTO):
    """安全扫描响应"""

    tool_id: str = Field(description="工具标识")
    version_id: str = Field(description="版本标识")
    scan_type: ScanType = Field(description="扫描类型")
    status: ScanStatus = Field(description="扫描状态")
    severity_counts: dict[str, int] = Field(description="各严重等级漏洞计数")
    vulnerabilities: list[dict[str, Any]] = Field(description="漏洞详情列表")
    scan_started_at: Optional[datetime] = Field(default=None, description="扫描开始时间")
    scan_completed_at: Optional[datetime] = Field(default=None, description="扫描完成时间")
    passed: bool = Field(description="是否通过扫描")


# =============================================================================
# 使用分析Schema
# =============================================================================


class UsageAnalyticsResponse(BaseDTO):
    """使用分析响应"""

    tool_id: str = Field(description="工具标识")
    total_calls: int = Field(description="总调用次数")
    success_count: int = Field(description="成功次数")
    failure_count: int = Field(description="失败次数")
    avg_latency_ms: float = Field(description="平均延迟（毫秒）")
    total_cost: float = Field(description="累计费用")
    last_used_at: Optional[datetime] = Field(default=None, description="最后使用时间")
    period_start: Optional[datetime] = Field(default=None, description="周期开始时间")
    period_end: Optional[datetime] = Field(default=None, description="周期结束时间")
    top_consumers: list[dict[str, Any]] = Field(description="主要调用方列表")
    success_rate: float = Field(description="成功率")


# =============================================================================
# 废弃Schema
# =============================================================================


class DeprecateToolRequest(CreateDTO):
    """废弃工具请求"""

    tool_id: str = Field(min_length=1, description="工具标识")
    reason: str = Field(min_length=1, description="废弃原因")
    sunset_date: Optional[datetime] = Field(default=None, description="计划下线日期")
    replacement_tool_id: Optional[str] = Field(default=None, description="替代工具标识")
    migration_guide: str = Field(default="", description="迁移指引")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class DeprecationResponse(BaseDTO):
    """废弃响应"""

    tool_id: str = Field(description="工具标识")
    reason: str = Field(description="废弃原因")
    deprecated_by: str = Field(description="发起人标识")
    deprecated_at: Optional[datetime] = Field(default=None, description="发起时间")
    sunset_date: Optional[datetime] = Field(default=None, description="计划下线日期")
    replacement_tool_id: Optional[str] = Field(default=None, description="替代工具标识")
    migration_guide: str = Field(description="迁移指引")
    status: DeprecationStatus = Field(description="废弃状态")


# =============================================================================
# 通用列表响应
# =============================================================================


class ReviewListResponse(BaseModel):
    """评审列表响应"""

    items: list[ReviewResponse] = Field(description="评审列表")
    total: int = Field(description="总数")


class ApprovalListResponse(BaseModel):
    """审批列表响应"""

    items: list[ApprovalResponse] = Field(description="审批列表")
    total: int = Field(description="总数")


class SecurityScanListResponse(BaseModel):
    """安全扫描列表响应"""

    items: list[SecurityScanResponse] = Field(description="安全扫描列表")
    total: int = Field(description="总数")


class UsageAnalyticsListResponse(BaseModel):
    """使用分析列表响应"""

    items: list[UsageAnalyticsResponse] = Field(description="使用分析列表")
    total: int = Field(description="总数")


class DeprecationListResponse(BaseModel):
    """废弃列表响应"""

    items: list[DeprecationResponse] = Field(description="废弃列表")
    total: int = Field(description="总数")
