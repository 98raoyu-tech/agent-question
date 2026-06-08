"""
治理中心 FastAPI路由

提供策略和审计日志管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.governance_service import GovernanceService
from ..domain.audit_log import AuditLog
from ..domain.enums import AuditAction
from ..domain.policy import Policy
from ..infrastructure.governance_repository import GovernanceRepository
from .schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    CreateAuditLogRequest,
    CreatePolicyRequest,
    PolicyListResponse,
    PolicyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/governance", tags=["治理中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_governance_repository = GovernanceRepository()
_governance_service = GovernanceService(_governance_repository)


# =============================================================================
# 策略端点
# =============================================================================


@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建策略",
    description="创建一个新的治理策略",
)
async def create_policy(request: CreatePolicyRequest) -> PolicyResponse:
    """创建策略"""
    try:
        policy = Policy(
            name=request.name,
            description=request.description,
            policy_type=request.policy_type,
            rules=request.rules,
            priority=request.priority,
            target_agents=request.target_agents,
            tenant_id=request.tenant_id,
        )

        created_policy = await _governance_service.create_policy(policy)

        return _to_policy_response(created_policy)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyResponse,
    summary="获取策略详情",
    description="根据ID获取策略的详细信息",
)
async def get_policy(policy_id: str) -> PolicyResponse:
    """获取策略详情"""
    try:
        policy = await _governance_service.get_policy(policy_id)
        return _to_policy_response(policy)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/policies",
    response_model=PolicyListResponse,
    summary="查询策略列表",
    description="分页查询策略列表",
)
async def list_policies(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> PolicyListResponse:
    """查询策略列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _governance_service.list_policies(pagination, tenant_id)

    return PolicyListResponse(
        items=[_to_policy_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除策略",
    description="软删除策略",
)
async def delete_policy(policy_id: str) -> None:
    """删除策略"""
    try:
        await _governance_service.delete_policy(policy_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 审计日志端点
# =============================================================================


@router.post(
    "/audit-logs",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建审计日志",
    description="记录一条审计日志",
)
async def create_audit_log(request: CreateAuditLogRequest) -> AuditLogResponse:
    """创建审计日志"""
    try:
        audit_log = AuditLog(
            user_id=request.user_id,
            action=request.action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            details=request.details,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            success=request.success,
            error_message=request.error_message,
            tenant_id=request.tenant_id,
        )

        created_log = await _governance_service.create_audit_log(audit_log)

        return _to_audit_log_response(created_log)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="查询审计日志",
    description="分页查询审计日志",
)
async def list_audit_logs(
    user_id: Optional[str] = Query(default=None, description="用户标识"),
    resource_type: Optional[str] = Query(default=None, description="资源类型"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AuditLogListResponse:
    """查询审计日志"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _governance_service.list_audit_logs(pagination, user_id, resource_type)

    return AuditLogListResponse(
        items=[_to_audit_log_response(l) for l in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_policy_response(policy: Policy) -> PolicyResponse:
    """将策略实体转换为响应Schema"""
    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        policy_type=policy.policy_type,
        status=policy.status,
        rules=policy.rules,
        priority=policy.priority,
        target_agents=policy.target_agents,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        tenant_id=policy.tenant_id,
    )


def _to_audit_log_response(audit_log: AuditLog) -> AuditLogResponse:
    """将审计日志实体转换为响应Schema"""
    return AuditLogResponse(
        id=audit_log.id,
        user_id=audit_log.user_id,
        action=audit_log.action,
        resource_type=audit_log.resource_type,
        resource_id=audit_log.resource_id,
        details=audit_log.details,
        ip_address=audit_log.ip_address,
        success=audit_log.success,
        error_message=audit_log.error_message,
        created_at=audit_log.created_at,
        updated_at=audit_log.updated_at,
        tenant_id=audit_log.tenant_id,
    )
