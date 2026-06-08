"""
Agent Ops FastAPI路由

提供Agent运维管理的RESTful API端点。
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
from ..application.agent_ops_service import AgentOpsService
from ..domain.enums import (
    DeploymentStatus,
    DeploymentStrategy,
    Environment,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
)
from ..domain.runbook import RunbookStep
from ..infrastructure.agent_ops_repository import AgentOpsRepository
from .schemas import (
    CreateDeploymentRequest,
    CreateIncidentRequest,
    CreateRunbookRequest,
    CreateSLARequest,
    CreateSLORequest,
    DeploymentListResponse,
    DeploymentResponse,
    ExecuteRunbookRequest,
    IncidentListResponse,
    IncidentResponse,
    PromoteCanaryRequest,
    RunbookExecutionResponse,
    RunbookListResponse,
    RunbookResponse,
    SLAListResponse,
    SLAResponse,
    SLOListResponse,
    SLOResponse,
    UpdateDeploymentRequest,
    UpdateIncidentStatusRequest,
    UpdateSLAMetricsRequest,
    UpdateSLOValueRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-ops", tags=["Agent Ops"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_agent_ops_repository = AgentOpsRepository()
_agent_ops_service = AgentOpsService(_agent_ops_repository)


# =============================================================================
# 部署端点
# =============================================================================


@router.post(
    "/deployments",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建部署",
    description="创建一个新的Agent部署",
)
async def create_deployment(request: CreateDeploymentRequest) -> DeploymentResponse:
    """创建部署

    Args:
        request: 创建部署请求

    Returns:
        创建的部署响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        deployment = await _agent_ops_service.create_deployment(
            agent_id=request.agent_id,
            version_id=request.version_id,
            environment=request.environment,
            strategy=request.strategy,
            config=request.config,
            operator=request.tenant_id,
        )

        return _to_deployment_response(deployment)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/deployments",
    response_model=DeploymentListResponse,
    summary="查询部署列表",
    description="分页查询部署列表",
)
async def list_deployments(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: Optional[str] = Query(default=None, description="Agent标识过滤"),
    environment: Optional[str] = Query(default=None, description="环境过滤"),
    deployment_status: Optional[str] = Query(default=None, alias="status", description="状态过滤"),
) -> DeploymentListResponse:
    """查询部署列表

    Args:
        page: 页码
        page_size: 每页大小
        agent_id: Agent标识过滤
        environment: 环境过滤
        deployment_status: 状态过滤

    Returns:
        部署列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    env_enum = Environment(environment) if environment else None
    status_enum = DeploymentStatus(deployment_status) if deployment_status else None

    result = await _agent_ops_service.list_deployments(
        pagination=pagination,
        agent_id=agent_id,
        environment=env_enum,
        status=status_enum,
    )

    return DeploymentListResponse(
        items=[_to_deployment_response(d) for d in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    summary="获取部署详情",
    description="根据ID获取部署的详细信息",
)
async def get_deployment(deployment_id: str) -> DeploymentResponse:
    """获取部署详情

    Args:
        deployment_id: 部署标识

    Returns:
        部署响应

    Raises:
        HTTPException: 部署不存在
    """
    try:
        deployment = await _agent_ops_service.get_deployment(deployment_id)
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    summary="更新部署",
    description="更新部署配置",
)
async def update_deployment(
    deployment_id: str,
    request: UpdateDeploymentRequest,
) -> DeploymentResponse:
    """更新部署

    Args:
        deployment_id: 部署标识
        request: 更新部署请求

    Returns:
        更新后的部署响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        deployment = await _agent_ops_service.update_deployment(
            deployment_id=deployment_id,
            config=request.config,
        )

        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/deployments/{deployment_id}/execute",
    response_model=DeploymentResponse,
    summary="执行部署",
    description="执行部署操作",
)
async def execute_deployment(deployment_id: str) -> DeploymentResponse:
    """执行部署

    Args:
        deployment_id: 部署标识

    Returns:
        部署响应

    Raises:
        HTTPException: 执行失败
    """
    try:
        deployment = await _agent_ops_service.execute_deployment(deployment_id)
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/deployments/{deployment_id}/rollback",
    response_model=DeploymentResponse,
    summary="回滚部署",
    description="回滚已激活的部署",
)
async def rollback_deployment(deployment_id: str) -> DeploymentResponse:
    """回滚部署

    Args:
        deployment_id: 部署标识

    Returns:
        回滚后的部署响应

    Raises:
        HTTPException: 回滚失败
    """
    try:
        deployment = await _agent_ops_service.rollback_deployment(deployment_id)
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/deployments/{deployment_id}/promote-canary",
    response_model=DeploymentResponse,
    summary="提升灰度比例",
    description="提升灰度发布的比例",
)
async def promote_canary(
    deployment_id: str,
    request: PromoteCanaryRequest,
) -> DeploymentResponse:
    """提升灰度比例

    Args:
        deployment_id: 部署标识
        request: 提升灰度比例请求

    Returns:
        更新后的部署响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        deployment = await _agent_ops_service.promote_canary(
            deployment_id=deployment_id,
            percentage=request.percentage,
        )

        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/deployments/{deployment_id}/switch-blue-green",
    response_model=DeploymentResponse,
    summary="切换蓝绿槽位",
    description="切换蓝绿部署的活跃槽位",
)
async def switch_blue_green(deployment_id: str) -> DeploymentResponse:
    """切换蓝绿槽位

    Args:
        deployment_id: 部署标识

    Returns:
        更新后的部署响应

    Raises:
        HTTPException: 操作失败
    """
    try:
        deployment = await _agent_ops_service.switch_blue_green(deployment_id)
        return _to_deployment_response(deployment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 事故端点
# =============================================================================


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建事故",
    description="创建一个新的事故",
)
async def create_incident(request: CreateIncidentRequest) -> IncidentResponse:
    """创建事故

    Args:
        request: 创建事故请求

    Returns:
        创建的事故响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        incident = await _agent_ops_service.create_incident(
            agent_id=request.agent_id,
            title=request.title,
            description=request.description,
            severity=request.severity,
            environment=request.environment,
            operator=request.tenant_id,
        )

        return _to_incident_response(incident)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    summary="查询事故列表",
    description="分页查询事故列表",
)
async def list_incidents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: Optional[str] = Query(default=None, description="Agent标识过滤"),
    severity: Optional[str] = Query(default=None, description="严重程度过滤"),
    incident_status: Optional[str] = Query(default=None, alias="status", description="状态过滤"),
) -> IncidentListResponse:
    """查询事故列表

    Args:
        page: 页码
        page_size: 每页大小
        agent_id: Agent标识过滤
        severity: 严重程度过滤
        incident_status: 状态过滤

    Returns:
        事故列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    severity_enum = IncidentSeverity(severity) if severity else None
    status_enum = IncidentStatus(incident_status) if incident_status else None

    result = await _agent_ops_service.list_incidents(
        pagination=pagination,
        agent_id=agent_id,
        severity=severity_enum,
        status=status_enum,
    )

    return IncidentListResponse(
        items=[_to_incident_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    summary="获取事故详情",
    description="根据ID获取事故的详细信息",
)
async def get_incident(incident_id: str) -> IncidentResponse:
    """获取事故详情

    Args:
        incident_id: 事故标识

    Returns:
        事故响应

    Raises:
        HTTPException: 事故不存在
    """
    try:
        incident = await _agent_ops_service.get_incident(incident_id)
        return _to_incident_response(incident)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/incidents/{incident_id}/status",
    response_model=IncidentResponse,
    summary="更新事故状态",
    description="更新事故的状态",
)
async def update_incident_status(
    incident_id: str,
    request: UpdateIncidentStatusRequest,
) -> IncidentResponse:
    """更新事故状态

    Args:
        incident_id: 事故标识
        request: 更新事故状态请求

    Returns:
        更新后的事故响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        incident = await _agent_ops_service.update_incident_status(
            incident_id=incident_id,
            new_status=request.status,
            root_cause=request.root_cause,
            resolution=request.resolution,
        )

        return _to_incident_response(incident)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =============================================================================
# 运维手册端点
# =============================================================================


@router.post(
    "/runbooks",
    response_model=RunbookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建运维手册",
    description="创建一个新的运维手册",
)
async def create_runbook(request: CreateRunbookRequest) -> RunbookResponse:
    """创建运维手册

    Args:
        request: 创建运维手册请求

    Returns:
        创建的运维手册响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        steps_data = [step.model_dump() for step in request.steps] if request.steps else None

        runbook = await _agent_ops_service.create_runbook(
            name=request.name,
            description=request.description,
            agent_id=request.agent_id,
            trigger_condition=request.trigger_condition,
            steps=steps_data,
            operator=request.tenant_id,
        )

        return _to_runbook_response(runbook)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/runbooks",
    response_model=RunbookListResponse,
    summary="查询运维手册列表",
    description="分页查询运维手册列表",
)
async def list_runbooks(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: Optional[str] = Query(default=None, description="Agent标识过滤"),
    is_active: Optional[bool] = Query(default=None, description="是否激活过滤"),
) -> RunbookListResponse:
    """查询运维手册列表

    Args:
        page: 页码
        page_size: 每页大小
        agent_id: Agent标识过滤
        is_active: 是否激活过滤

    Returns:
        运维手册列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _agent_ops_service.list_runbooks(
        pagination=pagination,
        agent_id=agent_id,
        is_active=is_active,
    )

    return RunbookListResponse(
        items=[_to_runbook_response(r) for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/runbooks/{runbook_id}",
    response_model=RunbookResponse,
    summary="获取运维手册详情",
    description="根据ID获取运维手册的详细信息",
)
async def get_runbook(runbook_id: str) -> RunbookResponse:
    """获取运维手册详情

    Args:
        runbook_id: 运维手册标识

    Returns:
        运维手册响应

    Raises:
        HTTPException: 运维手册不存在
    """
    try:
        runbook = await _agent_ops_service.get_runbook(runbook_id)
        return _to_runbook_response(runbook)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/runbooks/{runbook_id}/execute",
    response_model=RunbookExecutionResponse,
    summary="执行运维手册",
    description="执行指定的运维手册",
)
async def execute_runbook(
    runbook_id: str,
    request: ExecuteRunbookRequest,
) -> RunbookExecutionResponse:
    """执行运维手册

    Args:
        runbook_id: 运维手册标识
        request: 执行运维手册请求

    Returns:
        执行记录响应

    Raises:
        HTTPException: 执行失败
    """
    try:
        execution = await _agent_ops_service.execute_runbook(
            runbook_id=runbook_id,
            context=request.context,
        )

        return RunbookExecutionResponse(
            execution_id=execution.execution_id,
            executed_at=execution.executed_at,
            executed_by=execution.executed_by,
            context=execution.context,
            status=execution.status,
            result=execution.result,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# SLA端点
# =============================================================================


@router.post(
    "/sla",
    response_model=SLAResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建SLA",
    description="创建一个新的服务级别协议",
)
async def create_sla(request: CreateSLARequest) -> SLAResponse:
    """创建SLA

    Args:
        request: 创建SLA请求

    Returns:
        创建的SLA响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        sla = await _agent_ops_service.create_sla(
            name=request.name,
            agent_id=request.agent_id,
            target_uptime=request.target_uptime,
            target_latency_p99_ms=request.target_latency_p99_ms,
            target_success_rate=request.target_success_rate,
            target_availability=request.target_availability,
            period_days=request.period_days,
            operator=request.tenant_id,
        )

        return _to_sla_response(sla)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sla",
    response_model=SLAListResponse,
    summary="查询SLA列表",
    description="分页查询SLA列表",
)
async def list_slas(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: Optional[str] = Query(default=None, description="Agent标识过滤"),
) -> SLAListResponse:
    """查询SLA列表

    Args:
        page: 页码
        page_size: 每页大小
        agent_id: Agent标识过滤

    Returns:
        SLA列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _agent_ops_service.list_slas(
        pagination=pagination,
        agent_id=agent_id,
    )

    return SLAListResponse(
        items=[_to_sla_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/sla/{sla_id}",
    response_model=SLAResponse,
    summary="获取SLA详情",
    description="根据ID获取SLA的详细信息",
)
async def get_sla(sla_id: str) -> SLAResponse:
    """获取SLA详情

    Args:
        sla_id: SLA标识

    Returns:
        SLA响应

    Raises:
        HTTPException: SLA不存在
    """
    try:
        sla = await _agent_ops_service.get_sla(sla_id)
        return _to_sla_response(sla)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/sla/{sla_id}/metrics",
    response_model=SLAResponse,
    summary="更新SLA指标",
    description="更新SLA的当前指标值",
)
async def update_sla_metrics(
    sla_id: str,
    request: UpdateSLAMetricsRequest,
) -> SLAResponse:
    """更新SLA指标

    Args:
        sla_id: SLA标识
        request: 更新SLA指标请求

    Returns:
        更新后的SLA响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        sla = await _agent_ops_service.update_sla_metrics(
            sla_id=sla_id,
            uptime=request.uptime,
            latency=request.latency,
            success_rate=request.success_rate,
            availability=request.availability,
        )

        return _to_sla_response(sla)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# SLO端点
# =============================================================================


@router.post(
    "/slo",
    response_model=SLOResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建SLO",
    description="创建一个新的服务级别目标",
)
async def create_slo(request: CreateSLORequest) -> SLOResponse:
    """创建SLO

    Args:
        request: 创建SLO请求

    Returns:
        创建的SLO响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        slo = await _agent_ops_service.create_slo(
            name=request.name,
            agent_id=request.agent_id,
            sla_id=request.sla_id,
            metric_name=request.metric_name,
            target_value=request.target_value,
            period_days=request.period_days,
            operator=request.tenant_id,
        )

        return _to_slo_response(slo)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/slo",
    response_model=SLOListResponse,
    summary="查询SLO列表",
    description="分页查询SLO列表",
)
async def list_slos(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: Optional[str] = Query(default=None, description="Agent标识过滤"),
    sla_id: Optional[str] = Query(default=None, description="SLA标识过滤"),
) -> SLOListResponse:
    """查询SLO列表

    Args:
        page: 页码
        page_size: 每页大小
        agent_id: Agent标识过滤
        sla_id: SLA标识过滤

    Returns:
        SLO列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _agent_ops_service.list_slos(
        pagination=pagination,
        agent_id=agent_id,
        sla_id=sla_id,
    )

    return SLOListResponse(
        items=[_to_slo_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/slo/{slo_id}",
    response_model=SLOResponse,
    summary="获取SLO详情",
    description="根据ID获取SLO的详细信息",
)
async def get_slo(slo_id: str) -> SLOResponse:
    """获取SLO详情

    Args:
        slo_id: SLO标识

    Returns:
        SLO响应

    Raises:
        HTTPException: SLO不存在
    """
    try:
        slo = await _agent_ops_service.get_slo(slo_id)
        return _to_slo_response(slo)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.put(
    "/slo/{slo_id}/value",
    response_model=SLOResponse,
    summary="更新SLO当前值",
    description="更新SLO的当前指标值",
)
async def update_slo_value(
    slo_id: str,
    request: UpdateSLOValueRequest,
) -> SLOResponse:
    """更新SLO当前值

    Args:
        slo_id: SLO标识
        request: 更新SLO值请求

    Returns:
        更新后的SLO响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        slo = await _agent_ops_service.update_slo_value(
            slo_id=slo_id,
            value=request.value,
        )

        return _to_slo_response(slo)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_deployment_response(deployment: "Deployment") -> DeploymentResponse:
    """将部署实体转换为响应Schema

    Args:
        deployment: 部署实体

    Returns:
        部署响应
    """
    return DeploymentResponse(
        id=deployment.id,
        agent_id=deployment.agent_id,
        version_id=deployment.version_id,
        environment=deployment.environment,
        strategy=deployment.strategy,
        status=deployment.status,
        canary_percentage=deployment.canary_percentage,
        blue_green_active_slot=deployment.blue_green_active_slot,
        deployed_at=deployment.deployed_at,
        config=deployment.config,
        health_status=deployment.health_status,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at,
        tenant_id=deployment.tenant_id,
    )


def _to_incident_response(incident: "Incident") -> IncidentResponse:
    """将事故实体转换为响应Schema

    Args:
        incident: 事故实体

    Returns:
        事故响应
    """
    from .schemas import TimelineEntrySchema

    timeline = [
        TimelineEntrySchema(
            timestamp=entry.timestamp,
            action=entry.action,
            operator=entry.operator,
            details=entry.details,
        )
        for entry in incident.timeline
    ]

    return IncidentResponse(
        id=incident.id,
        agent_id=incident.agent_id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        assigned_to=incident.assigned_to,
        environment=incident.environment,
        detected_at=incident.detected_at,
        resolved_at=incident.resolved_at,
        root_cause=incident.root_cause,
        resolution=incident.resolution,
        timeline=timeline,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        tenant_id=incident.tenant_id,
    )


def _to_runbook_response(runbook: "Runbook") -> RunbookResponse:
    """将运维手册实体转换为响应Schema

    Args:
        runbook: 运维手册实体

    Returns:
        运维手册响应
    """
    from .schemas import RunbookStepSchema

    steps = [
        RunbookStepSchema(
            step_id=step.step_id,
            title=step.title,
            description=step.description,
            action_type=step.action_type,
            command=step.command,
            expected_result=step.expected_result,
        )
        for step in runbook.steps
    ]

    return RunbookResponse(
        id=runbook.id,
        name=runbook.name,
        description=runbook.description,
        agent_id=runbook.agent_id,
        trigger_condition=runbook.trigger_condition,
        steps=steps,
        is_active=runbook.is_active,
        last_executed_at=runbook.last_executed_at,
        execution_count=runbook.execution_count,
        created_at=runbook.created_at,
        updated_at=runbook.updated_at,
        tenant_id=runbook.tenant_id,
    )


def _to_sla_response(sla: "SLA") -> SLAResponse:
    """将SLA实体转换为响应Schema

    Args:
        sla: SLA实体

    Returns:
        SLA响应
    """
    from .schemas import SLAComplianceDetailsSchema

    compliance_details = sla.get_compliance_details()
    formatted_details = {
        key: SLAComplianceDetailsSchema(**value)
        for key, value in compliance_details.items()
    }

    return SLAResponse(
        id=sla.id,
        name=sla.name,
        agent_id=sla.agent_id,
        target_uptime=sla.target_uptime,
        target_latency_p99_ms=sla.target_latency_p99_ms,
        target_success_rate=sla.target_success_rate,
        target_availability=sla.target_availability,
        period_days=sla.period_days,
        current_uptime=sla.current_uptime,
        current_latency_p99=sla.current_latency_p99,
        current_success_rate=sla.current_success_rate,
        current_availability=sla.current_availability,
        is_met=sla.is_met,
        error_budget=sla.get_error_budget(),
        compliance_details=formatted_details,
        created_at=sla.created_at,
        updated_at=sla.updated_at,
        tenant_id=sla.tenant_id,
    )


def _to_slo_response(slo: "SLO") -> SLOResponse:
    """将SLO实体转换为响应Schema

    Args:
        slo: SLO实体

    Returns:
        SLO响应
    """
    return SLOResponse(
        id=slo.id,
        name=slo.name,
        agent_id=slo.agent_id,
        sla_id=slo.sla_id,
        metric_name=slo.metric_name,
        target_value=slo.target_value,
        current_value=slo.current_value,
        error_budget_remaining=slo.error_budget_remaining,
        burn_rate=slo.burn_rate,
        period_days=slo.period_days,
        is_burning_too_fast=slo.is_burning_too_fast(),
        remaining_days=slo.get_remaining_days(),
        created_at=slo.created_at,
        updated_at=slo.updated_at,
        tenant_id=slo.tenant_id,
    )
