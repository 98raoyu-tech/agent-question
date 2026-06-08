"""
知识治理 FastAPI路由

提供知识版本、审核、审批、发布和血缘管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Path, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ..application.knowledge_governance_service import KnowledgeGovernanceService
from ..domain.knowledge_approval import KnowledgeApproval
from ..domain.knowledge_lineage import KnowledgeLineage
from ..domain.knowledge_publish_record import KnowledgePublishRecord
from ..domain.knowledge_review import KnowledgeReview
from ..domain.knowledge_version import KnowledgeVersion
from ..infrastructure.knowledge_governance_repository import KnowledgeGovernanceRepository
from .knowledge_governance_schemas import (
    ApprovalActionRequest,
    ApprovalListResponse,
    ApprovalResponse,
    CreateVersionRequest,
    LineageListResponse,
    LineageResponse,
    PublishHistoryResponse,
    PublishRecordResponse,
    PublishVersionRequest,
    ReviewActionRequest,
    ReviewListResponse,
    ReviewResponse,
    RollbackPublishRequest,
    SubmitApprovalRequest,
    SubmitReviewRequest,
    VersionListResponse,
    VersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-governance", tags=["知识治理"])

_governance_repository = KnowledgeGovernanceRepository()
_governance_service = KnowledgeGovernanceService(_governance_repository)


# =============================================================================
# 版本端点
# =============================================================================


@router.post(
    "/versions",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建版本",
    description="为知识源创建新版本",
)
async def create_version(request: CreateVersionRequest) -> VersionResponse:
    """创建知识版本

    Args:
        request: 创建版本请求

    Returns:
        创建的版本响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        version = await _governance_service.create_version(
            source_id=request.source_id,
            change_log=request.change_log,
            snapshot=request.snapshot,
            operator=request.tenant_id,
        )
        return _to_version_response(version)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sources/{source_id}/versions",
    response_model=VersionListResponse,
    summary="查询版本列表",
    description="查询知识源下的所有版本",
)
async def list_versions(
    source_id: str = Path(description="知识源标识"),
) -> VersionListResponse:
    """查询知识源下的版本列表

    Args:
        source_id: 知识源标识

    Returns:
        版本列表响应
    """
    versions = await _governance_service.get_versions(source_id)

    return VersionListResponse(
        items=[_to_version_response(v) for v in versions],
        total=len(versions),
    )


# =============================================================================
# 审核端点
# =============================================================================


@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交审核",
    description="为版本提交审核",
)
async def submit_review(request: SubmitReviewRequest) -> ReviewResponse:
    """提交版本审核

    Args:
        request: 提交审核请求

    Returns:
        创建的审核响应

    Raises:
        HTTPException: 提交失败
    """
    try:
        review = await _governance_service.submit_review(
            version_id=request.version_id,
            reviewer_id=request.reviewer_id,
            operator=request.tenant_id,
        )
        return _to_review_response(review)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/reviews/{review_id}/approve",
    response_model=ReviewResponse,
    summary="通过审核",
    description="通过指定的审核记录",
)
async def approve_review(
    review_id: str = Path(description="审核标识"),
    request: ReviewActionRequest = ...,
) -> ReviewResponse:
    """通过审核

    Args:
        review_id: 审核标识
        request: 审核操作请求

    Returns:
        更新后的审核响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        review = await _governance_service.approve_review(
            review_id=review_id,
            reviewer=request.reviewer,
            notes=request.notes,
        )
        return _to_review_response(review)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/reviews/{review_id}/reject",
    response_model=ReviewResponse,
    summary="驳回审核",
    description="驳回指定的审核记录",
)
async def reject_review(
    review_id: str = Path(description="审核标识"),
    request: ReviewActionRequest = ...,
) -> ReviewResponse:
    """驳回审核

    Args:
        review_id: 审核标识
        request: 审核操作请求

    Returns:
        更新后的审核响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        review = await _governance_service.reject_review(
            review_id=review_id,
            reviewer=request.reviewer,
            reason=request.notes,
        )
        return _to_review_response(review)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 审批端点
# =============================================================================


@router.post(
    "/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交审批",
    description="为已通过审核的版本提交审批",
)
async def submit_approval(request: SubmitApprovalRequest) -> ApprovalResponse:
    """提交版本审批

    Args:
        request: 提交审批请求

    Returns:
        创建的审批响应

    Raises:
        HTTPException: 提交失败
    """
    try:
        approval = await _governance_service.submit_approval(
            version_id=request.version_id,
            requester=request.requester,
            operator=request.tenant_id,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
    summary="批准审批",
    description="批准指定的审批记录",
)
async def approve_version(
    approval_id: str = Path(description="审批标识"),
    request: ApprovalActionRequest = ...,
) -> ApprovalResponse:
    """批准版本审批

    Args:
        approval_id: 审批标识
        request: 审批操作请求

    Returns:
        更新后的审批响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        approval = await _governance_service.approve_version(
            approval_id=approval_id,
            approver=request.approver,
            notes=request.notes,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalResponse,
    summary="驳回审批",
    description="驳回指定的审批记录",
)
async def reject_approval(
    approval_id: str = Path(description="审批标识"),
    request: ApprovalActionRequest = ...,
) -> ApprovalResponse:
    """驳回版本审批

    Args:
        approval_id: 审批标识
        request: 审批操作请求

    Returns:
        更新后的审批响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        approval = await _governance_service.reject_approval(
            approval_id=approval_id,
            approver=request.approver,
            reason=request.notes,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 发布端点
# =============================================================================


@router.post(
    "/publish",
    response_model=PublishRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发布版本",
    description="发布已批准的版本",
)
async def publish_version(request: PublishVersionRequest) -> PublishRecordResponse:
    """发布版本

    Args:
        request: 发布版本请求

    Returns:
        发布记录响应

    Raises:
        HTTPException: 发布失败
    """
    try:
        record = await _governance_service.publish_version(
            version_id=request.version_id,
            environment=request.environment,
            operator=request.tenant_id,
        )
        return _to_publish_record_response(record)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/publish/{publish_id}/rollback",
    response_model=PublishRecordResponse,
    summary="回滚发布",
    description="将已发布的版本回滚到指定目标版本",
)
async def rollback_publish(
    publish_id: str = Path(description="发布记录标识"),
    request: RollbackPublishRequest = ...,
) -> PublishRecordResponse:
    """回滚发布

    Args:
        publish_id: 发布记录标识
        request: 回滚请求

    Returns:
        更新后的发布记录响应

    Raises:
        HTTPException: 回滚失败
    """
    try:
        record = await _governance_service.rollback_publish(
            publish_id=publish_id,
            target_version_id=request.target_version_id,
        )
        return _to_publish_record_response(record)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sources/{source_id}/publish-history",
    response_model=PublishHistoryResponse,
    summary="查询发布历史",
    description="查询知识源下的所有发布记录",
)
async def get_publish_history(
    source_id: str = Path(description="知识源标识"),
) -> PublishHistoryResponse:
    """查询发布历史

    Args:
        source_id: 知识源标识

    Returns:
        发布历史响应
    """
    records = await _governance_service.get_publish_history(source_id)

    return PublishHistoryResponse(
        items=[_to_publish_record_response(r) for r in records],
        total=len(records),
    )


# =============================================================================
# 血缘端点
# =============================================================================


@router.get(
    "/sources/{source_id}/lineage",
    response_model=LineageListResponse,
    summary="查询血缘关系",
    description="查询知识源下的所有版本血缘关系",
)
async def get_lineage(
    source_id: str = Path(description="知识源标识"),
) -> LineageListResponse:
    """查询知识源的血缘关系

    Args:
        source_id: 知识源标识

    Returns:
        血缘关系列表响应
    """
    lineages = await _governance_service.get_lineage(source_id)

    return LineageListResponse(
        items=[_to_lineage_response(l) for l in lineages],
        total=len(lineages),
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_version_response(version: KnowledgeVersion) -> VersionResponse:
    """将版本实体转换为响应Schema

    Args:
        version: 版本实体

    Returns:
        版本响应
    """
    return VersionResponse(
        id=version.id,
        knowledge_source_id=version.knowledge_source_id,
        version_number=version.version_number,
        change_log=version.change_log,
        snapshot=version.snapshot,
        is_current=version.is_current,
        status=version.status,
        created_at=version.created_at,
        updated_at=version.updated_at,
        tenant_id=version.tenant_id,
    )


def _to_review_response(review: KnowledgeReview) -> ReviewResponse:
    """将审核实体转换为响应Schema

    Args:
        review: 审核实体

    Returns:
        审核响应
    """
    return ReviewResponse(
        id=review.id,
        knowledge_source_id=review.knowledge_source_id,
        version_id=review.version_id,
        reviewer_id=review.reviewer_id,
        status=review.status,
        review_notes=review.review_notes,
        reviewed_at=review.reviewed_at,
        review_criteria=review.review_criteria,
        quality_score=review.quality_score,
        created_at=review.created_at,
        updated_at=review.updated_at,
        tenant_id=review.tenant_id,
    )


def _to_approval_response(approval: KnowledgeApproval) -> ApprovalResponse:
    """将审批实体转换为响应Schema

    Args:
        approval: 审批实体

    Returns:
        审批响应
    """
    return ApprovalResponse(
        id=approval.id,
        knowledge_source_id=approval.knowledge_source_id,
        version_id=approval.version_id,
        requested_by=approval.requested_by,
        approved_by=approval.approved_by,
        status=approval.status,
        requested_at=approval.requested_at,
        approved_at=approval.approved_at,
        approval_chain=approval.approval_chain,
        rejection_reason=approval.rejection_reason,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
        tenant_id=approval.tenant_id,
    )


def _to_publish_record_response(record: KnowledgePublishRecord) -> PublishRecordResponse:
    """将发布记录实体转换为响应Schema

    Args:
        record: 发布记录实体

    Returns:
        发布记录响应
    """
    return PublishRecordResponse(
        id=record.id,
        knowledge_source_id=record.knowledge_source_id,
        version_id=record.version_id,
        published_by=record.published_by,
        published_at=record.published_at,
        environment=record.environment,
        status=record.status,
        rollback_version_id=record.rollback_version_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        tenant_id=record.tenant_id,
    )


def _to_lineage_response(lineage: KnowledgeLineage) -> LineageResponse:
    """将血缘实体转换为响应Schema

    Args:
        lineage: 血缘实体

    Returns:
        血缘响应
    """
    return LineageResponse(
        id=lineage.id,
        source_id=lineage.source_id,
        parent_version_id=lineage.parent_version_id,
        child_version_id=lineage.child_version_id,
        transformation_type=lineage.transformation_type,
        transformation_details=lineage.transformation_details,
        created_at=lineage.created_at,
        updated_at=lineage.updated_at,
        tenant_id=lineage.tenant_id,
    )
