"""
工具生命周期 FastAPI路由

提供工具评审、审批、安全扫描、使用分析和废弃管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ..application.tool_lifecycle_service import ToolLifecycleService
from ..domain.tool_security_scan import ScanType
from ..infrastructure.tool_lifecycle_repository import ToolLifecycleRepository
from .tool_lifecycle_schemas import (
    ApprovalActionRequest,
    ApprovalListResponse,
    ApprovalResponse,
    DeprecateToolRequest,
    DeprecationListResponse,
    DeprecationResponse,
    ReviewActionRequest,
    ReviewListResponse,
    ReviewResponse,
    RunSecurityScanRequest,
    SecurityScanListResponse,
    SecurityScanResponse,
    SubmitApprovalRequest,
    SubmitReviewRequest,
    UsageAnalyticsListResponse,
    UsageAnalyticsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tool-lifecycle", tags=["工具生命周期"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_lifecycle_repository = ToolLifecycleRepository()
_lifecycle_service = ToolLifecycleService(_lifecycle_repository)


# ========== 评审端点 ==========


@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交评审",
    description="为指定工具提交评审请求",
)
async def submit_review(request: SubmitReviewRequest) -> ReviewResponse:
    """提交工具评审"""
    try:
        review = await _lifecycle_service.submit_review(
            tool_id=request.tool_id,
            operator=request.operator,
        )
        return _to_review_response(review)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/reviews/{review_id}/approve",
    response_model=ReviewResponse,
    summary="通过评审",
    description="评审人通过指定评审",
)
async def approve_review(review_id: str, request: ReviewActionRequest) -> ReviewResponse:
    """通过评审"""
    try:
        review = await _lifecycle_service.approve_review(
            review_id=review_id,
            reviewer=request.reviewer,
            notes=request.notes,
        )
        return _to_review_response(review)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/reviews/{review_id}/reject",
    response_model=ReviewResponse,
    summary="驳回评审",
    description="评审人驳回指定评审",
)
async def reject_review(review_id: str, request: ReviewActionRequest) -> ReviewResponse:
    """驳回评审"""
    try:
        review = await _lifecycle_service.reject_review(
            review_id=review_id,
            reviewer=request.reviewer,
            reason=request.notes,
        )
        return _to_review_response(review)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools/{tool_id}/reviews",
    response_model=ReviewListResponse,
    summary="查询评审列表",
    description="获取指定工具的所有评审记录",
)
async def list_reviews(tool_id: str) -> ReviewListResponse:
    """查询工具评审列表"""
    reviews = await _lifecycle_service.get_reviews(tool_id)
    return ReviewListResponse(
        items=[_to_review_response(r) for r in reviews],
        total=len(reviews),
    )


# ========== 审批端点 ==========


@router.post(
    "/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交审批",
    description="为指定工具版本提交审批请求",
)
async def submit_approval(request: SubmitApprovalRequest) -> ApprovalResponse:
    """提交工具审批"""
    try:
        approval = await _lifecycle_service.submit_approval(
            tool_id=request.tool_id,
            version_id=request.version_id,
            operator=request.operator,
        )
        return _to_approval_response(approval)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
    summary="批准工具",
    description="审批人批准指定的审批请求",
)
async def approve_tool(approval_id: str, request: ApprovalActionRequest) -> ApprovalResponse:
    """批准工具"""
    try:
        approval = await _lifecycle_service.approve_tool(
            approval_id=approval_id,
            approver=request.approver,
            notes=request.notes,
        )
        return _to_approval_response(approval)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools/{tool_id}/approvals",
    response_model=ApprovalListResponse,
    summary="查询审批历史",
    description="获取指定工具的所有审批记录",
)
async def list_approvals(tool_id: str) -> ApprovalListResponse:
    """查询工具审批历史"""
    approvals = await _lifecycle_service.get_approval_history(tool_id)
    return ApprovalListResponse(
        items=[_to_approval_response(a) for a in approvals],
        total=len(approvals),
    )


# ========== 安全扫描端点 ==========


@router.post(
    "/security-scans",
    response_model=SecurityScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="启动安全扫描",
    description="为指定工具版本启动安全扫描",
)
async def run_security_scan(request: RunSecurityScanRequest) -> SecurityScanResponse:
    """启动安全扫描"""
    try:
        scan = await _lifecycle_service.run_security_scan(
            tool_id=request.tool_id,
            version_id=request.version_id,
            scan_type=request.scan_type,
            operator=request.operator,
        )
        return _to_security_scan_response(scan)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools/{tool_id}/security-scans",
    response_model=SecurityScanListResponse,
    summary="查询安全扫描记录",
    description="获取指定工具的所有安全扫描记录",
)
async def list_security_scans(tool_id: str) -> SecurityScanListResponse:
    """查询工具安全扫描记录"""
    scans = await _lifecycle_service.get_security_scans(tool_id)
    return SecurityScanListResponse(
        items=[_to_security_scan_response(s) for s in scans],
        total=len(scans),
    )


# ========== 使用分析端点 ==========


@router.get(
    "/tools/{tool_id}/analytics",
    response_model=UsageAnalyticsListResponse,
    summary="查询使用分析",
    description="获取指定工具的使用统计数据",
)
async def get_usage_analytics(
    tool_id: str,
    period_start: Optional[str] = Query(default=None, description="周期开始时间"),
    period_end: Optional[str] = Query(default=None, description="周期结束时间"),
) -> UsageAnalyticsListResponse:
    """查询工具使用分析"""
    analytics = await _lifecycle_service.get_usage_analytics(
        tool_id, period_start, period_end,
    )
    return UsageAnalyticsListResponse(
        items=[_to_usage_analytics_response(a) for a in analytics],
        total=len(analytics),
    )


# ========== 废弃端点 ==========


@router.post(
    "/deprecations",
    response_model=DeprecationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="废弃工具",
    description="为指定工具创建废弃计划",
)
async def deprecate_tool(request: DeprecateToolRequest) -> DeprecationResponse:
    """废弃工具"""
    try:
        deprecation = await _lifecycle_service.deprecate_tool(
            tool_id=request.tool_id,
            reason=request.reason,
            sunset_date=request.sunset_date,
            operator=request.operator,
            replacement_tool_id=request.replacement_tool_id,
            migration_guide=request.migration_guide,
        )
        return _to_deprecation_response(deprecation)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools/{tool_id}/deprecations",
    response_model=DeprecationListResponse,
    summary="查询废弃信息",
    description="获取指定工具的所有废弃记录",
)
async def list_deprecations(tool_id: str) -> DeprecationListResponse:
    """查询工具废弃信息"""
    deprecations = await _lifecycle_service.repository.find_deprecations_by_tool(tool_id)
    return DeprecationListResponse(
        items=[_to_deprecation_response(d) for d in deprecations],
        total=len(deprecations),
    )


# ========== 实体到响应的转换函数 ==========


def _to_review_response(review) -> ReviewResponse:
    """将评审实体转换为响应Schema"""
    return ReviewResponse(
        id=review.id,
        tool_id=review.tool_id,
        reviewer_id=review.reviewer_id,
        status=review.status,
        review_notes=review.review_notes,
        reviewed_at=review.reviewed_at,
        criteria_scores=review.criteria_scores,
        overall_score=review.overall_score,
        created_at=review.created_at,
        updated_at=review.updated_at,
        tenant_id=review.tenant_id,
    )


def _to_approval_response(approval) -> ApprovalResponse:
    """将审批实体转换为响应Schema"""
    return ApprovalResponse(
        id=approval.id,
        tool_id=approval.tool_id,
        version_id=approval.version_id,
        requested_by=approval.requested_by,
        approved_by=approval.approved_by,
        status=approval.status,
        requested_at=approval.requested_at,
        approved_at=approval.approved_at,
        approval_notes=approval.approval_notes,
        rejection_reason=approval.rejection_reason,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
        tenant_id=approval.tenant_id,
    )


def _to_security_scan_response(scan) -> SecurityScanResponse:
    """将安全扫描实体转换为响应Schema"""
    return SecurityScanResponse(
        id=scan.id,
        tool_id=scan.tool_id,
        version_id=scan.version_id,
        scan_type=scan.scan_type,
        status=scan.status,
        severity_counts=scan.severity_counts,
        vulnerabilities=scan.vulnerabilities,
        scan_started_at=scan.scan_started_at,
        scan_completed_at=scan.scan_completed_at,
        passed=scan.passed,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        tenant_id=scan.tenant_id,
    )


def _to_usage_analytics_response(analytics) -> UsageAnalyticsResponse:
    """将使用分析实体转换为响应Schema"""
    return UsageAnalyticsResponse(
        id=analytics.id,
        tool_id=analytics.tool_id,
        total_calls=analytics.total_calls,
        success_count=analytics.success_count,
        failure_count=analytics.failure_count,
        avg_latency_ms=analytics.avg_latency_ms,
        total_cost=analytics.total_cost,
        last_used_at=analytics.last_used_at,
        period_start=analytics.period_start,
        period_end=analytics.period_end,
        top_consumers=analytics.top_consumers,
        success_rate=analytics.get_success_rate(),
        created_at=analytics.created_at,
        updated_at=analytics.updated_at,
        tenant_id=analytics.tenant_id,
    )


def _to_deprecation_response(deprecation) -> DeprecationResponse:
    """将废弃实体转换为响应Schema"""
    return DeprecationResponse(
        id=deprecation.id,
        tool_id=deprecation.tool_id,
        reason=deprecation.reason,
        deprecated_by=deprecation.deprecated_by,
        deprecated_at=deprecation.deprecated_at,
        sunset_date=deprecation.sunset_date,
        replacement_tool_id=deprecation.replacement_tool_id,
        migration_guide=deprecation.migration_guide,
        status=deprecation.status,
        created_at=deprecation.created_at,
        updated_at=deprecation.updated_at,
        tenant_id=deprecation.tenant_id,
    )
