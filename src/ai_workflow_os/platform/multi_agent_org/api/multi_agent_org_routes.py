"""
多智能体组织 FastAPI路由

提供Agent注册、消息通信、任务委托、团队管理和任务管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Path, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.multi_agent_org_service import MultiAgentOrgService
from ..domain.agent_communication import AgentMessage
from ..domain.agent_delegation import AgentDelegation
from ..domain.agent_registry import AgentRegistryEntry
from ..domain.agent_task import AgentTask
from ..domain.agent_team import AgentTeam
from ..domain.enums import AgentRole, CommunicationType
from ..infrastructure.multi_agent_org_repository import MultiAgentOrgRepository
from .schemas import (
    AddTeamMemberRequest,
    AgentDelegationResponse,
    AgentMessageListResponse,
    AgentMessageResponse,
    AgentRegistryListResponse,
    AgentRegistryResponse,
    AgentTaskResponse,
    AgentTeamListResponse,
    AgentTeamResponse,
    AssignTaskRequest,
    CompleteDelegationRequest,
    CompleteTaskRequest,
    CreateTaskRequest,
    CreateTeamRequest,
    DelegateTaskRequest,
    RegisterAgentRequest,
    SendMessageRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multi-agent-org", tags=["多智能体组织"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_multi_agent_org_repository = MultiAgentOrgRepository()
_multi_agent_org_service = MultiAgentOrgService(_multi_agent_org_repository)


# =============================================================================
# 实体转换函数
# =============================================================================


def _to_agent_response(entry: AgentRegistryEntry) -> AgentRegistryResponse:
    """将Agent注册条目转换为响应DTO"""
    return AgentRegistryResponse(
        id=entry.id,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        tenant_id=entry.tenant_id,
        agent_id=entry.agent_id,
        agent_name=entry.agent_name,
        agent_role=entry.agent_role,
        capabilities=entry.capabilities,
        status=entry.status,
        endpoint_url=entry.endpoint_url,
        max_concurrent_tasks=entry.max_concurrent_tasks,
        current_task_count=entry.current_task_count,
        metadata=entry.metadata,
    )


def _to_message_response(message: AgentMessage) -> AgentMessageResponse:
    """将消息转换为响应DTO"""
    return AgentMessageResponse(
        id=message.id,
        created_at=message.created_at,
        updated_at=message.updated_at,
        tenant_id=message.tenant_id,
        sender_agent_id=message.sender_agent_id,
        receiver_agent_id=message.receiver_agent_id,
        communication_type=message.communication_type,
        subject=message.subject,
        content=message.content,
        priority=message.priority,
        correlation_id=message.correlation_id,
        status=message.status,
        sent_at=message.sent_at,
        delivered_at=message.delivered_at,
        read_at=message.read_at,
        reply_to_id=message.reply_to_id,
    )


def _to_delegation_response(delegation: AgentDelegation) -> AgentDelegationResponse:
    """将委托转换为响应DTO"""
    return AgentDelegationResponse(
        id=delegation.id,
        created_at=delegation.created_at,
        updated_at=delegation.updated_at,
        tenant_id=delegation.tenant_id,
        delegator_agent_id=delegation.delegator_agent_id,
        delegate_agent_id=delegation.delegate_agent_id,
        task_description=delegation.task_description,
        task_context=delegation.task_context,
        status=delegation.status,
        delegated_at=delegation.delegated_at,
        accepted_at=delegation.accepted_at,
        completed_at=delegation.completed_at,
        result=delegation.result,
        error_message=delegation.error_message,
        priority=delegation.priority,
    )


def _to_team_response(team: AgentTeam) -> AgentTeamResponse:
    """将团队转换为响应DTO"""
    return AgentTeamResponse(
        id=team.id,
        created_at=team.created_at,
        updated_at=team.updated_at,
        tenant_id=team.tenant_id,
        name=team.name,
        description=team.description,
        team_status=team.team_status,
        leader_agent_id=team.leader_agent_id,
        member_ids=team.member_ids,
        member_roles=team.member_roles,
        capabilities=team.capabilities,
        max_members=team.max_members,
        active_delegation_ids=team.active_delegation_ids,
    )


def _to_task_response(task: AgentTask) -> AgentTaskResponse:
    """将任务转换为响应DTO"""
    return AgentTaskResponse(
        id=task.id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        tenant_id=task.tenant_id,
        title=task.title,
        description=task.description,
        assigned_agent_id=task.assigned_agent_id,
        team_id=task.team_id,
        status=task.status,
        priority=task.priority,
        context=task.context,
        result=task.result,
        parent_task_id=task.parent_task_id,
        sub_task_ids=task.sub_task_ids,
        deadline=task.deadline,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
    )


# =============================================================================
# Agent注册端点
# =============================================================================


@router.post(
    "/agents/register",
    response_model=AgentRegistryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册Agent",
    description="注册一个新的Agent到多智能体组织",
)
async def register_agent(request: RegisterAgentRequest) -> AgentRegistryResponse:
    """注册Agent

    Args:
        request: 注册Agent请求

    Returns:
        Agent注册响应

    Raises:
        HTTPException: 注册失败
    """
    try:
        entry = AgentRegistryEntry(
            agent_id=request.agent_id,
            agent_name=request.agent_name,
            agent_role=request.agent_role,
            capabilities=request.capabilities,
            endpoint_url=request.endpoint_url,
            max_concurrent_tasks=request.max_concurrent_tasks,
            metadata=request.metadata,
            tenant_id=request.tenant_id,
        )
        result = await _multi_agent_org_service.register_agent(entry, operator=request.created_by)
        return _to_agent_response(result)

    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/agents/{agent_id}/deregister",
    response_model=AgentRegistryResponse,
    summary="注销Agent",
    description="注销指定的Agent",
)
async def deregister_agent(agent_id: str) -> AgentRegistryResponse:
    """注销Agent

    Args:
        agent_id: Agent标识

    Returns:
        注销后的Agent注册响应

    Raises:
        HTTPException: 注销失败
    """
    try:
        result = await _multi_agent_org_service.deregister_agent(agent_id)
        return _to_agent_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/discover",
    response_model=AgentRegistryListResponse,
    summary="发现Agent",
    description="根据能力和角色条件筛选可用的Agent",
)
async def discover_agents(
    capability: str | None = Query(default=None, description="能力过滤"),
    role: AgentRole | None = Query(default=None, description="角色过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AgentRegistryListResponse:
    """发现Agent

    Args:
        capability: 能力过滤
        role: 角色过滤
        page: 页码
        page_size: 每页大小

    Returns:
        Agent注册列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _multi_agent_org_service.discover_agents(
        capability=capability,
        role=role,
        pagination=pagination,
    )
    return AgentRegistryListResponse(
        items=[_to_agent_response(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/agents",
    response_model=AgentRegistryListResponse,
    summary="列出所有Agent",
    description="分页查询Agent注册列表",
)
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AgentRegistryListResponse:
    """列出所有Agent

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        Agent注册列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _multi_agent_org_service.list_agents(pagination=pagination)
    return AgentRegistryListResponse(
        items=[_to_agent_response(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 消息通信端点
# =============================================================================


@router.post(
    "/messages",
    response_model=AgentMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发送消息",
    description="发送一条Agent间的消息",
)
async def send_message(request: SendMessageRequest) -> AgentMessageResponse:
    """发送消息

    Args:
        request: 发送消息请求

    Returns:
        消息响应

    Raises:
        HTTPException: 发送失败
    """
    try:
        message = AgentMessage(
            sender_agent_id=request.sender_agent_id,
            receiver_agent_id=request.receiver_agent_id,
            communication_type=request.communication_type,
            subject=request.subject,
            content=request.content,
            priority=request.priority,
            correlation_id=request.correlation_id,
            reply_to_id=request.reply_to_id,
            tenant_id=request.tenant_id,
        )
        result = await _multi_agent_org_service.send_message(message, operator=request.created_by)
        return _to_message_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}/messages",
    response_model=AgentMessageListResponse,
    summary="获取Agent消息",
    description="获取指定Agent的消息列表",
)
async def get_agent_messages(
    agent_id: str = Path(description="Agent标识"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AgentMessageListResponse:
    """获取Agent消息列表

    Args:
        agent_id: Agent标识
        page: 页码
        page_size: 每页大小

    Returns:
        消息列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _multi_agent_org_service.get_messages(agent_id, pagination)
    return AgentMessageListResponse(
        items=[_to_message_response(m) for m in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 委托端点
# =============================================================================


@router.post(
    "/delegations",
    response_model=AgentDelegationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="委托任务",
    description="创建一个新的任务委托",
)
async def delegate_task(request: DelegateTaskRequest) -> AgentDelegationResponse:
    """委托任务

    Args:
        request: 委托任务请求

    Returns:
        委托响应

    Raises:
        HTTPException: 委托失败
    """
    try:
        delegation = AgentDelegation(
            delegator_agent_id=request.delegator_agent_id,
            delegate_agent_id=request.delegate_agent_id,
            task_description=request.task_description,
            task_context=request.task_context,
            priority=request.priority,
            tenant_id=request.tenant_id,
        )
        result = await _multi_agent_org_service.delegate_task(delegation, operator=request.created_by)
        return _to_delegation_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/delegations/{delegation_id}/accept",
    response_model=AgentDelegationResponse,
    summary="接受委托",
    description="接受指定的任务委托",
)
async def accept_delegation(
    delegation_id: str = Path(description="委托标识"),
) -> AgentDelegationResponse:
    """接受委托

    Args:
        delegation_id: 委托标识

    Returns:
        更新后的委托响应

    Raises:
        HTTPException: 接受失败
    """
    try:
        result = await _multi_agent_org_service.accept_delegation(delegation_id)
        return _to_delegation_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/delegations/{delegation_id}/complete",
    response_model=AgentDelegationResponse,
    summary="完成委托",
    description="完成指定的任务委托",
)
async def complete_delegation(
    delegation_id: str = Path(description="委托标识"),
    request: CompleteDelegationRequest = ...,
) -> AgentDelegationResponse:
    """完成委托

    Args:
        delegation_id: 委托标识
        request: 完成委托请求

    Returns:
        更新后的委托响应

    Raises:
        HTTPException: 完成失败
    """
    try:
        result = await _multi_agent_org_service.complete_delegation(delegation_id, request.result)
        return _to_delegation_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 团队端点
# =============================================================================


@router.post(
    "/teams",
    response_model=AgentTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建团队",
    description="创建一个新的Agent团队",
)
async def create_team(request: CreateTeamRequest) -> AgentTeamResponse:
    """创建团队

    Args:
        request: 创建团队请求

    Returns:
        团队响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        team = AgentTeam(
            name=request.name,
            description=request.description,
            capabilities=request.capabilities,
            max_members=request.max_members,
            tenant_id=request.tenant_id,
        )
        result = await _multi_agent_org_service.create_team(team, operator=request.created_by)
        return _to_team_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/teams/{team_id}/members",
    response_model=AgentTeamResponse,
    summary="添加团队成员",
    description="向指定团队添加成员",
)
async def add_team_member(
    team_id: str = Path(description="团队标识"),
    request: AddTeamMemberRequest = ...,
) -> AgentTeamResponse:
    """添加团队成员

    Args:
        team_id: 团队标识
        request: 添加成员请求

    Returns:
        更新后的团队响应

    Raises:
        HTTPException: 添加失败
    """
    try:
        result = await _multi_agent_org_service.add_team_member(
            team_id, request.agent_id, request.role,
        )
        return _to_team_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/teams/{team_id}/disband",
    response_model=AgentTeamResponse,
    summary="解散团队",
    description="解散指定的Agent团队",
)
async def disband_team(
    team_id: str = Path(description="团队标识"),
) -> AgentTeamResponse:
    """解散团队

    Args:
        team_id: 团队标识

    Returns:
        更新后的团队响应

    Raises:
        HTTPException: 解散失败
    """
    try:
        result = await _multi_agent_org_service.disband_team(team_id)
        return _to_team_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/teams",
    response_model=AgentTeamListResponse,
    summary="列出所有团队",
    description="分页查询Agent团队列表",
)
async def list_teams(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AgentTeamListResponse:
    """列出所有团队

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        团队列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _multi_agent_org_service.list_teams(pagination=pagination)
    return AgentTeamListResponse(
        items=[_to_team_response(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/teams/{team_id}",
    response_model=AgentTeamResponse,
    summary="获取团队状态",
    description="获取指定团队的详细状态",
)
async def get_team_status(
    team_id: str = Path(description="团队标识"),
) -> AgentTeamResponse:
    """获取团队状态

    Args:
        team_id: 团队标识

    Returns:
        团队响应

    Raises:
        HTTPException: 获取失败
    """
    try:
        result = await _multi_agent_org_service.get_team_status(team_id)
        return _to_team_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 任务端点
# =============================================================================


@router.post(
    "/tasks",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建任务",
    description="创建一个新的协作任务",
)
async def create_task(request: CreateTaskRequest) -> AgentTaskResponse:
    """创建任务

    Args:
        request: 创建任务请求

    Returns:
        任务响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        task = AgentTask(
            title=request.title,
            description=request.description,
            team_id=request.team_id,
            priority=request.priority,
            context=request.context,
            parent_task_id=request.parent_task_id,
            deadline=request.deadline,
            tenant_id=request.tenant_id,
        )
        result = await _multi_agent_org_service.create_task(task, operator=request.created_by)
        return _to_task_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/tasks/{task_id}/assign",
    response_model=AgentTaskResponse,
    summary="分配任务",
    description="将任务分配给指定Agent",
)
async def assign_task(
    task_id: str = Path(description="任务标识"),
    request: AssignTaskRequest = ...,
) -> AgentTaskResponse:
    """分配任务

    Args:
        task_id: 任务标识
        request: 分配任务请求

    Returns:
        更新后的任务响应

    Raises:
        HTTPException: 分配失败
    """
    try:
        result = await _multi_agent_org_service.assign_task(task_id, request.agent_id)
        return _to_task_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/tasks/{task_id}/complete",
    response_model=AgentTaskResponse,
    summary="完成任务",
    description="标记任务为已完成",
)
async def complete_task(
    task_id: str = Path(description="任务标识"),
    request: CompleteTaskRequest = ...,
) -> AgentTaskResponse:
    """完成任务

    Args:
        task_id: 任务标识
        request: 完成任务请求

    Returns:
        更新后的任务响应

    Raises:
        HTTPException: 完成失败
    """
    try:
        result = await _multi_agent_org_service.complete_task(task_id, request.result)
        return _to_task_response(result)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
