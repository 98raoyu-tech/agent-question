"""
Agent Registry FastAPI路由

提供Agent注册管理的RESTful API端点。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.agent_registry_service import AgentRegistryService
from ..domain.agent_registration import AgentRegistration
from ..domain.agent_runtime_info import AgentRuntimeInfo
from ..infrastructure.agent_registry_repository import AgentRegistryRepository
from .schemas import (
    AgentRegistrationListResponse,
    AgentRegistrationResponse,
    AgentRuntimeInfoResponse,
    RegisterAgentRequest,
    UpdateAgentRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-registry", tags=["Agent Registry"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_agent_registry_repository = AgentRegistryRepository()
_agent_registry_service = AgentRegistryService(_agent_registry_repository)


# =============================================================================
# Agent注册CRUD端点
# =============================================================================


@router.post(
    "/agents",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册Agent",
    description="注册一个新的Agent到注册中心",
)
async def register_agent(request: RegisterAgentRequest) -> AgentRegistrationResponse:
    """注册Agent

    Args:
        request: 注册Agent请求

    Returns:
        注册的Agent响应

    Raises:
        HTTPException: 注册失败
    """
    try:
        # 构建领域实体
        registration = AgentRegistration(
            name=request.name,
            description=request.description,
            version=request.version,
            framework=request.framework,
            model_name=request.model_name,
            owner_id=request.owner_id,
            team_id=request.team_id,
            endpoint=request.endpoint,
            tags=request.tags,
            metadata=request.metadata,
            capabilities=request.capabilities,
            tenant_id=request.tenant_id,
        )

        # 调用服务注册
        created_registration = await _agent_registry_service.register_agent(registration, request.created_by)

        return _to_registration_response(created_registration)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents",
    response_model=AgentRegistrationListResponse,
    summary="查询Agent注册列表",
    description="分页查询Agent注册列表",
)
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    status_filter: str | None = Query(default=None, alias="status", description="状态过滤"),
    framework: str | None = Query(default=None, description="框架类型过滤"),
    owner_id: str | None = Query(default=None, description="所有者标识过滤"),
    team_id: str | None = Query(default=None, description="团队标识过滤"),
    search: str | None = Query(default=None, description="搜索关键词"),
    tenant_id: str | None = Query(default=None, description="租户标识"),
) -> AgentRegistrationListResponse:
    """查询Agent注册列表

    Args:
        page: 页码
        page_size: 每页大小
        status_filter: 状态过滤
        framework: 框架类型过滤
        owner_id: 所有者标识过滤
        team_id: 团队标识过滤
        search: 搜索关键词
        tenant_id: 租户标识

    Returns:
        Agent注册列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    # 构建过滤条件
    filters: dict[str, Any] = {}
    if status_filter:
        filters["status"] = status_filter
    if framework:
        filters["framework"] = framework
    if owner_id:
        filters["owner_id"] = owner_id
    if team_id:
        filters["team_id"] = team_id
    if search:
        filters["search"] = search

    result = await _agent_registry_service.list_agents(pagination, tenant_id, filters)

    return AgentRegistrationListResponse(
        items=[_to_registration_response(r) for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentRegistrationResponse,
    summary="获取Agent注册详情",
    description="根据ID获取Agent注册的详细信息",
)
async def get_agent(agent_id: str) -> AgentRegistrationResponse:
    """获取Agent注册详情

    Args:
        agent_id: Agent注册标识

    Returns:
        Agent注册响应

    Raises:
        HTTPException: Agent不存在
    """
    try:
        registration = await _agent_registry_service.get_agent(agent_id)
        return _to_registration_response(registration)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/agents/{agent_id}",
    response_model=AgentRegistrationResponse,
    summary="更新Agent注册信息",
    description="更新Agent注册信息",
)
async def update_agent(agent_id: str, request: UpdateAgentRequest) -> AgentRegistrationResponse:
    """更新Agent注册信息

    Args:
        agent_id: Agent注册标识
        request: 更新Agent请求

    Returns:
        更新后的Agent注册响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        # 构建更新字典
        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.version is not None:
            updates["version"] = request.version
        if request.framework is not None:
            updates["framework"] = request.framework
        if request.model_name is not None:
            updates["model_name"] = request.model_name
        if request.owner_id is not None:
            updates["owner_id"] = request.owner_id
        if request.team_id is not None:
            updates["team_id"] = request.team_id
        if request.endpoint is not None:
            updates["endpoint"] = request.endpoint
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.metadata is not None:
            updates["metadata"] = request.metadata
        if request.capabilities is not None:
            updates["capabilities"] = request.capabilities

        # 调用服务更新
        updated_registration = await _agent_registry_service.update_agent(agent_id, updates)

        return _to_registration_response(updated_registration)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="注销Agent",
    description="软删除Agent注册信息",
)
async def deregister_agent(agent_id: str) -> None:
    """注销Agent

    Args:
        agent_id: Agent注册标识

    Raises:
        HTTPException: 注销失败
    """
    try:
        await _agent_registry_service.deregister_agent(agent_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# Agent心跳和运行时信息端点
# =============================================================================


@router.post(
    "/agents/{agent_id}/heartbeat",
    response_model=AgentRuntimeInfoResponse,
    summary="Agent实例心跳",
    description="上报Agent实例的心跳信息",
)
async def heartbeat(
    agent_id: str,
    instance_id: str = Query(description="运行实例标识"),
) -> AgentRuntimeInfoResponse:
    """Agent实例心跳

    Args:
        agent_id: Agent注册标识
        instance_id: 运行实例标识

    Returns:
        运行时信息响应

    Raises:
        HTTPException: 心跳失败
    """
    try:
        runtime_info = await _agent_registry_service.heartbeat(agent_id, instance_id)
        return _to_runtime_info_response(runtime_info)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}/runtime",
    response_model=list[AgentRuntimeInfoResponse],
    summary="获取Agent运行时信息",
    description="获取Agent关联的所有运行时实例信息",
)
async def get_runtime_infos(agent_id: str) -> list[AgentRuntimeInfoResponse]:
    """获取Agent运行时信息

    Args:
        agent_id: Agent注册标识

    Returns:
        运行时信息列表响应

    Raises:
        HTTPException: Agent不存在
    """
    try:
        runtime_infos = await _agent_registry_service.get_runtime_infos(agent_id)
        return [_to_runtime_info_response(info) for info in runtime_infos]

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_registration_response(registration: AgentRegistration) -> AgentRegistrationResponse:
    """将Agent注册实体转换为响应Schema

    Args:
        registration: Agent注册实体

    Returns:
        Agent注册响应
    """
    return AgentRegistrationResponse(
        id=registration.id,
        name=registration.name,
        description=registration.description,
        version=registration.version,
        framework=registration.framework,
        model_name=registration.model_name,
        owner_id=registration.owner_id,
        team_id=registration.team_id,
        endpoint=registration.endpoint,
        status=registration.status,
        health_status=registration.health_status,
        tags=registration.tags,
        metadata=registration.metadata,
        capabilities=registration.capabilities,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
        tenant_id=registration.tenant_id,
    )


def _to_runtime_info_response(runtime_info: AgentRuntimeInfo) -> AgentRuntimeInfoResponse:
    """将运行时信息实体转换为响应Schema

    Args:
        runtime_info: 运行时信息实体

    Returns:
        运行时信息响应
    """
    return AgentRuntimeInfoResponse(
        id=runtime_info.id,
        agent_registration_id=runtime_info.agent_registration_id,
        instance_id=runtime_info.instance_id,
        host=runtime_info.host,
        port=runtime_info.port,
        pid=runtime_info.pid,
        uptime_seconds=runtime_info.uptime_seconds,
        request_count=runtime_info.request_count,
        error_count=runtime_info.error_count,
        avg_latency_ms=runtime_info.avg_latency_ms,
        last_heartbeat=runtime_info.last_heartbeat,
        status=runtime_info.status,
        error_rate=runtime_info.error_rate,
        is_responsive=runtime_info.is_responsive,
        created_at=runtime_info.created_at,
        updated_at=runtime_info.updated_at,
        tenant_id=runtime_info.tenant_id,
    )
