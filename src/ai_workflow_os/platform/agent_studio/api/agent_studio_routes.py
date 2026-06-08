"""
Agent Studio FastAPI路由

提供Agent管理的RESTful API端点。
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
from ...common.pagination import PaginatedRequest
from ..application.agent_service import AgentService
from ..domain.agent_definition import (
    AgentDefinition,
    KnowledgeSourceConfig,
    ModelConfig,
    ToolConfig,
)
from ..infrastructure.agent_repository import AgentRepository
from .schemas import (
    AgentListResponse,
    AgentReleaseResponse,
    AgentResponse,
    CreateAgentRequest,
    PublishAgentRequest,
    UpdateAgentRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-studio", tags=["Agent Studio"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_agent_repository = AgentRepository()
_agent_service = AgentService(_agent_repository)


# =============================================================================
# Agent CRUD端点
# =============================================================================


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建Agent",
    description="创建一个新的Agent定义",
)
async def create_agent(request: CreateAgentRequest) -> AgentResponse:
    """创建Agent

    Args:
        request: 创建Agent请求

    Returns:
        创建的Agent响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        # 构建领域实体
        agent = _build_agent_from_request(request)

        # 调用服务创建
        created_agent = await _agent_service.create_agent(agent, request.created_by)

        return _to_agent_response(created_agent)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="获取Agent详情",
    description="根据ID获取Agent的详细信息",
)
async def get_agent(agent_id: str) -> AgentResponse:
    """获取Agent详情

    Args:
        agent_id: Agent标识

    Returns:
        Agent响应

    Raises:
        HTTPException: Agent不存在
    """
    try:
        agent = await _agent_service.get_agent(agent_id)
        return _to_agent_response(agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="查询Agent列表",
    description="分页查询Agent列表",
)
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="状态过滤"),
    agent_type: Optional[str] = Query(default=None, description="Agent类型过滤"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> AgentListResponse:
    """查询Agent列表

    Args:
        page: 页码
        page_size: 每页大小
        status_filter: 状态过滤
        agent_type: Agent类型过滤
        search: 搜索关键词
        tenant_id: 租户标识

    Returns:
        Agent列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    # 构建过滤条件
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if agent_type:
        filters["agent_type"] = agent_type
    if search:
        filters["search"] = search

    result = await _agent_service.repository.find_all(pagination, tenant_id, filters)

    return AgentListResponse(
        items=[_to_agent_response(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="更新Agent",
    description="更新Agent定义信息",
)
async def update_agent(agent_id: str, request: UpdateAgentRequest) -> AgentResponse:
    """更新Agent

    Args:
        agent_id: Agent标识
        request: 更新Agent请求

    Returns:
        更新后的Agent响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        # 获取现有Agent
        existing_agent = await _agent_service.get_agent(agent_id)

        # 更新字段
        if request.name is not None:
            existing_agent.name = request.name
        if request.description is not None:
            existing_agent.description = request.description
        if request.agent_type is not None:
            existing_agent.agent_type = request.agent_type
        if request.system_prompt is not None:
            existing_agent.system_prompt = request.system_prompt
        if request.llm_config is not None:
            existing_agent.model_config = ModelConfig(
                model_name=request.llm_config.model_name,
                temperature=request.llm_config.temperature,
                max_tokens=request.llm_config.max_tokens,
                top_p=request.llm_config.top_p,
                extra_params=request.llm_config.extra_params,
            )
        if request.tools is not None:
            existing_agent.tools = [
                ToolConfig(
                    tool_id=t.tool_id,
                    tool_name=t.tool_name,
                    tool_type=t.tool_type,
                    description=t.description,
                    parameters=t.parameters,
                    is_required=t.is_required,
                )
                for t in request.tools
            ]
        if request.knowledge_sources is not None:
            existing_agent.knowledge_sources = [
                KnowledgeSourceConfig(
                    source_id=s.source_id,
                    source_name=s.source_name,
                    source_type=s.source_type,
                    retrieval_config=s.retrieval_config,
                    is_enabled=s.is_enabled,
                )
                for s in request.knowledge_sources
            ]
        if request.tags is not None:
            existing_agent.tags = request.tags
        if request.metadata is not None:
            existing_agent.metadata = request.metadata

        # 调用服务更新
        updated_agent = await _agent_service.update_agent(agent_id, existing_agent)

        return _to_agent_response(updated_agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除Agent",
    description="软删除Agent",
)
async def delete_agent(agent_id: str) -> None:
    """删除Agent

    Args:
        agent_id: Agent标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _agent_service.delete_agent(agent_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# Agent发布端点
# =============================================================================


@router.post(
    "/agents/{agent_id}/publish",
    response_model=AgentReleaseResponse,
    summary="发布Agent",
    description="发布Agent到生产环境",
)
async def publish_agent(
    agent_id: str,
    request: PublishAgentRequest = PublishAgentRequest(),
) -> AgentReleaseResponse:
    """发布Agent

    Args:
        agent_id: Agent标识
        request: 发布请求

    Returns:
        发布响应

    Raises:
        HTTPException: 发布失败
    """
    try:
        release = await _agent_service.publish_agent(
            agent_id=agent_id,
            release_name=request.release_name,
            release_notes=request.release_notes,
        )

        return AgentReleaseResponse(
            id=release.id,
            agent_id=release.agent_id,
            version_id=release.version_id,
            release_name=release.release_name,
            status=release.status.value,
            release_notes=release.release_notes,
            rollout_percentage=release.rollout_percentage,
            released_at=release.released_at,
            created_at=release.created_at,
            updated_at=release.updated_at,
            tenant_id=release.tenant_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/agents/{agent_id}/archive",
    response_model=AgentResponse,
    summary="归档Agent",
    description="归档Agent",
)
async def archive_agent(agent_id: str) -> AgentResponse:
    """归档Agent

    Args:
        agent_id: Agent标识

    Returns:
        归档后的Agent响应

    Raises:
        HTTPException: 归档失败
    """
    try:
        agent = await _agent_service.archive_agent(agent_id)
        return _to_agent_response(agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _build_agent_from_request(request: CreateAgentRequest) -> AgentDefinition:
    """从请求构建Agent实体

    Args:
        request: 创建Agent请求

    Returns:
        Agent实体
    """
    model_config = ModelConfig(
        model_name=request.llm_config.model_name,
        temperature=request.llm_config.temperature,
        max_tokens=request.llm_config.max_tokens,
        top_p=request.llm_config.top_p,
        extra_params=request.llm_config.extra_params,
    )

    tools = [
        ToolConfig(
            tool_id=t.tool_id,
            tool_name=t.tool_name,
            tool_type=t.tool_type,
            description=t.description,
            parameters=t.parameters,
            is_required=t.is_required,
        )
        for t in request.tools
    ]

    knowledge_sources = [
        KnowledgeSourceConfig(
            source_id=s.source_id,
            source_name=s.source_name,
            source_type=s.source_type,
            retrieval_config=s.retrieval_config,
            is_enabled=s.is_enabled,
        )
        for s in request.knowledge_sources
    ]

    return AgentDefinition(
        name=request.name,
        description=request.description,
        agent_type=request.agent_type,
        system_prompt=request.system_prompt,
        model_config=model_config,
        tools=tools,
        knowledge_sources=knowledge_sources,
        tags=request.tags,
        metadata=request.metadata,
        tenant_id=request.tenant_id,
    )


def _to_agent_response(agent: AgentDefinition) -> AgentResponse:
    """将Agent实体转换为响应Schema

    Args:
        agent: Agent实体

    Returns:
        Agent响应
    """
    from .schemas import KnowledgeSourceConfigSchema, ModelConfigResponse, ToolConfigSchema

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type,
        status=agent.status,
        system_prompt=agent.system_prompt,
        llm_config=ModelConfigResponse(
            model_name=agent.model_config.model_name,
            temperature=agent.model_config.temperature,
            max_tokens=agent.model_config.max_tokens,
            top_p=agent.model_config.top_p,
        ),
        tools=[
            ToolConfigSchema(
                tool_id=t.tool_id,
                tool_name=t.tool_name,
                tool_type=t.tool_type,
                description=t.description,
                parameters=t.parameters,
                is_required=t.is_required,
            )
            for t in agent.tools
        ],
        knowledge_sources=[
            KnowledgeSourceConfigSchema(
                source_id=s.source_id,
                source_name=s.source_name,
                source_type=s.source_type,
                retrieval_config=s.retrieval_config,
                is_enabled=s.is_enabled,
            )
            for s in agent.knowledge_sources
        ],
        tags=agent.tags,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        tenant_id=agent.tenant_id,
    )
