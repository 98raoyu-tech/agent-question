"""
Agent Lifecycle FastAPI路由

提供Agent生命周期管理的RESTful API端点，包括CRUD操作、状态转换、
版本管理、测试、评估、审批、部署和回滚操作。
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
from ..application.agent_lifecycle_service import AgentLifecycleService
from ..domain.agent_definition import AgentLifecycleDefinition
from ..domain.enums import (
    AgentLifecycleState,
    DeploymentEnvironment,
    DeploymentStrategy,
    TestType,
)
from ..infrastructure.agent_lifecycle_repository import AgentLifecycleRepository
from .schemas import (
    AgentLifecycleListResponse,
    AgentLifecycleResponse,
    AgentVersionResponse,
    ApprovalResponse,
    ApproveVersionRequest,
    CreateAgentLifecycleRequest,
    CreateVersionRequest,
    DeploymentResponse,
    DeployVersionRequest,
    EvaluationResponse,
    RejectVersionRequest,
    RollbackDeploymentRequest,
    RollbackResponse,
    SubmitApprovalRequest,
    SubmitEvaluationRequest,
    SubmitTestingRequest,
    TestRunResponse,
    TransitionStateRequest,
    UpdateAgentLifecycleRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-lifecycle", tags=["Agent Lifecycle"])

_agent_repository = AgentLifecycleRepository()
_agent_lifecycle_service = AgentLifecycleService(_agent_repository)


# =============================================================================
# Agent CRUD端点
# =============================================================================


@router.post(
    "/agents",
    response_model=AgentLifecycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建Agent",
    description="创建一个新的Agent生命周期定义",
)
async def create_agent(request: CreateAgentLifecycleRequest) -> AgentLifecycleResponse:
    """创建Agent"""
    try:
        agent = AgentLifecycleDefinition(
            name=request.name,
            description=request.description,
            owner_id=request.owner_id,
            team_id=request.team_id,
            tags=request.tags,
            metadata=request.metadata,
            tenant_id=request.tenant_id,
        )
        created_agent = await _agent_lifecycle_service.create_agent(agent, request.tenant_id)
        return _to_agent_response(created_agent)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentLifecycleResponse,
    summary="获取Agent详情",
    description="根据ID获取Agent生命周期定义的详细信息",
)
async def get_agent(agent_id: str) -> AgentLifecycleResponse:
    """获取Agent详情"""
    try:
        agent = await _agent_lifecycle_service.get_agent(agent_id)
        return _to_agent_response(agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents",
    response_model=AgentLifecycleListResponse,
    summary="查询Agent列表",
    description="分页查询Agent生命周期定义列表",
)
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    lifecycle_state: Optional[str] = Query(default=None, description="生命周期状态过滤"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> AgentLifecycleListResponse:
    """查询Agent列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)

    filters = {}
    if lifecycle_state:
        filters["lifecycle_state"] = lifecycle_state
    if search:
        filters["search"] = search

    result = await _agent_lifecycle_service.list_agents(pagination, tenant_id, filters)

    return AgentLifecycleListResponse(
        items=[_to_agent_response(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/agents/{agent_id}",
    response_model=AgentLifecycleResponse,
    summary="更新Agent",
    description="更新Agent生命周期定义信息",
)
async def update_agent(
    agent_id: str,
    request: UpdateAgentLifecycleRequest,
) -> AgentLifecycleResponse:
    """更新Agent"""
    try:
        existing_agent = await _agent_lifecycle_service.get_agent(agent_id)

        if request.name is not None:
            existing_agent.name = request.name
        if request.description is not None:
            existing_agent.description = request.description
        if request.owner_id is not None:
            existing_agent.owner_id = request.owner_id
        if request.team_id is not None:
            existing_agent.team_id = request.team_id
        if request.tags is not None:
            existing_agent.tags = request.tags
        if request.metadata is not None:
            existing_agent.metadata = request.metadata

        updated_agent = await _agent_lifecycle_service.update_agent(
            agent_id,
            existing_agent,
            request.version,
        )
        return _to_agent_response(updated_agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 状态转换端点
# =============================================================================


@router.post(
    "/agents/{agent_id}/transition",
    response_model=AgentLifecycleResponse,
    summary="状态转换",
    description="执行Agent生命周期状态转换",
)
async def transition_state(
    agent_id: str,
    request: TransitionStateRequest,
) -> AgentLifecycleResponse:
    """执行Agent状态转换"""
    try:
        agent = await _agent_lifecycle_service.transition_state(
            agent_id,
            request.target_state,
            request.operator,
        )
        return _to_agent_response(agent)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 版本管理端点
# =============================================================================


@router.post(
    "/agents/{agent_id}/versions",
    response_model=AgentVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建版本",
    description="为Agent创建新版本",
)
async def create_version(
    agent_id: str,
    request: CreateVersionRequest = CreateVersionRequest(),
) -> AgentVersionResponse:
    """创建Agent版本"""
    try:
        version = await _agent_lifecycle_service.create_version(
            agent_id,
            request.change_log,
            request.operator,
        )
        return _to_version_response(version)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}/versions",
    response_model=list[AgentVersionResponse],
    summary="查询版本列表",
    description="查询Agent的版本列表",
)
async def list_versions(
    agent_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> list[AgentVersionResponse]:
    """查询Agent版本列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    versions = await _agent_lifecycle_service.list_versions(agent_id, pagination)
    return [_to_version_response(v) for v in versions]


# =============================================================================
# 测试端点
# =============================================================================


@router.post(
    "/versions/{version_id}/testing",
    response_model=TestRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交测试",
    description="提交Agent版本进行测试",
)
async def submit_for_testing(
    version_id: str,
    request: SubmitTestingRequest = SubmitTestingRequest(),
) -> TestRunResponse:
    """提交版本进行测试"""
    try:
        test_run = await _agent_lifecycle_service.submit_for_testing(
            version_id,
            request.test_name,
            request.test_type,
            request.operator,
        )
        return _to_test_run_response(test_run)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 评估端点
# =============================================================================


@router.post(
    "/versions/{version_id}/evaluation",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交评估",
    description="提交Agent版本进行评估",
)
async def submit_for_evaluation(
    version_id: str,
    request: SubmitEvaluationRequest = SubmitEvaluationRequest(),
) -> EvaluationResponse:
    """提交版本进行评估"""
    try:
        evaluation = await _agent_lifecycle_service.submit_for_evaluation(
            version_id,
            request.evaluation_name,
            request.operator,
        )
        return _to_evaluation_response(evaluation)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 审批端点
# =============================================================================


@router.post(
    "/versions/{version_id}/approval",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交审批",
    description="提交Agent版本进行审批",
)
async def submit_for_approval(
    version_id: str,
    request: SubmitApprovalRequest,
) -> ApprovalResponse:
    """提交版本进行审批"""
    try:
        approval = await _agent_lifecycle_service.submit_for_approval(
            version_id,
            request.requested_by,
            request.operator,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/versions/{version_id}/approve",
    response_model=ApprovalResponse,
    summary="批准版本",
    description="批准Agent版本",
)
async def approve_version(
    version_id: str,
    request: ApproveVersionRequest,
) -> ApprovalResponse:
    """批准版本"""
    try:
        approval = await _agent_lifecycle_service.approve_version(
            version_id,
            request.reviewer,
            request.notes,
            request.operator,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/versions/{version_id}/reject",
    response_model=ApprovalResponse,
    summary="拒绝版本",
    description="拒绝Agent版本",
)
async def reject_version(
    version_id: str,
    request: RejectVersionRequest,
) -> ApprovalResponse:
    """拒绝版本"""
    try:
        approval = await _agent_lifecycle_service.reject_version(
            version_id,
            request.reviewer,
            request.reason,
            request.operator,
        )
        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 部署端点
# =============================================================================


@router.post(
    "/versions/{version_id}/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="部署版本",
    description="部署Agent版本到指定环境",
)
async def deploy_version(
    version_id: str,
    request: DeployVersionRequest = DeployVersionRequest(),
) -> DeploymentResponse:
    """部署版本"""
    try:
        deployment = await _agent_lifecycle_service.deploy_version(
            version_id,
            request.environment,
            request.deployment_strategy,
            request.operator,
        )
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    summary="获取部署状态",
    description="获取部署的状态详情",
)
async def get_deployment_status(deployment_id: str) -> DeploymentResponse:
    """获取部署状态"""
    try:
        deployment = await _agent_lifecycle_service.get_deployment_status(deployment_id)
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/agents/{agent_id}/deployments",
    response_model=list[DeploymentResponse],
    summary="查询部署列表",
    description="查询Agent的部署列表",
)
async def list_deployments(
    agent_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> list[DeploymentResponse]:
    """查询Agent部署列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    deployments = await _agent_lifecycle_service.list_deployments(agent_id, pagination)
    return [_to_deployment_response(d) for d in deployments]


# =============================================================================
# 回滚端点
# =============================================================================


@router.post(
    "/deployments/{deployment_id}/rollback",
    response_model=RollbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="回滚部署",
    description="回滚指定的部署",
)
async def rollback_deployment(
    deployment_id: str,
    request: RollbackDeploymentRequest = RollbackDeploymentRequest(),
) -> RollbackResponse:
    """回滚部署"""
    try:
        rollback = await _agent_lifecycle_service.rollback_deployment(
            deployment_id,
            request.reason,
            request.to_version_id,
            request.operator,
        )
        return _to_rollback_response(rollback)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_agent_response(agent: AgentLifecycleDefinition) -> AgentLifecycleResponse:
    """将Agent实体转换为响应Schema"""
    return AgentLifecycleResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        lifecycle_state=agent.lifecycle_state,
        current_version_id=agent.current_version_id,
        owner_id=agent.owner_id,
        team_id=agent.team_id,
        tags=agent.tags,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        tenant_id=agent.tenant_id,
    )


def _to_version_response(version) -> AgentVersionResponse:
    """将版本实体转换为响应Schema"""
    return AgentVersionResponse(
        id=version.id,
        agent_id=version.agent_id,
        version_number=version.version_number,
        change_log=version.change_log,
        is_current=version.is_current,
        lifecycle_state=version.lifecycle_state,
        approval_status=version.approval_status,
        approved_by=version.approved_by,
        approved_at=version.approved_at,
        rejection_reason=version.rejection_reason,
        created_at=version.created_at,
        updated_at=version.updated_at,
        tenant_id=version.tenant_id,
    )


def _to_test_run_response(test_run) -> TestRunResponse:
    """将测试运行实体转换为响应Schema"""
    return TestRunResponse(
        id=test_run.id,
        agent_id=test_run.agent_id,
        version_id=test_run.version_id,
        test_name=test_run.test_name,
        status=test_run.status,
        test_type=test_run.test_type,
        started_at=test_run.started_at,
        completed_at=test_run.completed_at,
        error_message=test_run.error_message,
        pass_rate=test_run.pass_rate,
        created_at=test_run.created_at,
        updated_at=test_run.updated_at,
        tenant_id=test_run.tenant_id,
    )


def _to_evaluation_response(evaluation) -> EvaluationResponse:
    """将评估实体转换为响应Schema"""
    return EvaluationResponse(
        id=evaluation.id,
        agent_id=evaluation.agent_id,
        version_id=evaluation.version_id,
        evaluation_name=evaluation.evaluation_name,
        status=evaluation.status,
        accuracy=evaluation.accuracy,
        latency_ms=evaluation.latency_ms,
        cost=evaluation.cost,
        success_rate=evaluation.success_rate,
        hallucination_rate=evaluation.hallucination_rate,
        groundedness_score=evaluation.groundedness_score,
        safety_score=evaluation.safety_score,
        overall_score=evaluation.overall_score,
        passed=evaluation.passed,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
        tenant_id=evaluation.tenant_id,
    )


def _to_approval_response(approval) -> ApprovalResponse:
    """将审批实体转换为响应Schema"""
    return ApprovalResponse(
        id=approval.id,
        agent_id=approval.agent_id,
        version_id=approval.version_id,
        approval_status=approval.approval_status,
        requested_by=approval.requested_by,
        reviewed_by=approval.reviewed_by,
        review_notes=approval.review_notes,
        requested_at=approval.requested_at,
        reviewed_at=approval.reviewed_at,
        approval_chain=approval.approval_chain,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
        tenant_id=approval.tenant_id,
    )


def _to_deployment_response(deployment) -> DeploymentResponse:
    """将部署实体转换为响应Schema"""
    return DeploymentResponse(
        id=deployment.id,
        agent_id=deployment.agent_id,
        version_id=deployment.version_id,
        environment=deployment.environment,
        deployment_strategy=deployment.deployment_strategy,
        status=deployment.status,
        deployed_at=deployment.deployed_at,
        rolled_back_at=deployment.rolled_back_at,
        health_check_url=deployment.health_check_url,
        traffic_percentage=deployment.traffic_percentage,
        replicas=deployment.replicas,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at,
        tenant_id=deployment.tenant_id,
    )


def _to_rollback_response(rollback) -> RollbackResponse:
    """将回滚实体转换为响应Schema"""
    return RollbackResponse(
        id=rollback.id,
        agent_id=rollback.agent_id,
        from_version_id=rollback.from_version_id,
        to_version_id=rollback.to_version_id,
        reason=rollback.reason,
        status=rollback.status,
        initiated_by=rollback.initiated_by,
        completed_at=rollback.completed_at,
        error_message=rollback.error_message,
        created_at=rollback.created_at,
        updated_at=rollback.updated_at,
        tenant_id=rollback.tenant_id,
    )
