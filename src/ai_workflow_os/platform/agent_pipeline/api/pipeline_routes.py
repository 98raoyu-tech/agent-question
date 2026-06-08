"""
Agent Pipeline FastAPI路由

提供Agent发布流水线管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.pipeline_service import AgentPipelineService
from ..infrastructure.pipeline_repository import AgentPipelineRepository
from .schemas import (
    ApproveReleaseRequest,
    DeployReleaseRequest,
    ExecuteStageRequest,
    PipelineListResponse,
    PipelineResponse,
    PipelineStepResponse,
    RejectReleaseRequest,
    RollbackReleaseRequest,
    StartPipelineRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-pipeline", tags=["Agent Pipeline"])

_pipeline_repository = AgentPipelineRepository()
_pipeline_service = AgentPipelineService(_pipeline_repository)


# =============================================================================
# 流水线端点
# =============================================================================


@router.post(
    "/pipelines",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="启动发布流水线",
    description="创建并启动一个Agent发布流水线，确保所有发布必须经过Pipeline",
)
async def start_pipeline(request: StartPipelineRequest) -> PipelineResponse:
    """启动发布流水线"""
    try:
        pipeline = await _pipeline_service.start_release_pipeline(
            agent_id=request.agent_id,
            version_id=request.version_id,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/pipelines/{pipeline_id}",
    response_model=PipelineResponse,
    summary="获取流水线详情",
    description="根据ID获取Agent发布流水线的详细信息",
)
async def get_pipeline(pipeline_id: str) -> PipelineResponse:
    """获取流水线详情"""
    try:
        pipeline = await _pipeline_service.get_pipeline(pipeline_id)
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/pipelines",
    response_model=PipelineListResponse,
    summary="查询流水线列表",
    description="分页查询Agent发布流水线列表",
)
async def list_pipelines(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    agent_id: str | None = Query(default=None, description="Agent标识过滤"),
    pipeline_status: str | None = Query(default=None, description="状态过滤"),
    tenant_id: str | None = Query(default=None, description="租户标识"),
) -> PipelineListResponse:
    """查询流水线列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)

    filters = {}
    if agent_id:
        filters["agent_id"] = agent_id
    if pipeline_status:
        filters["status"] = pipeline_status

    result = await _pipeline_service.list_pipelines(pagination, tenant_id, filters)

    return PipelineListResponse(
        items=[_to_pipeline_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 阶段执行端点
# =============================================================================


@router.post(
    "/pipelines/{pipeline_id}/execute",
    response_model=PipelineResponse,
    summary="执行当前阶段",
    description="完成当前阶段并推进到下一阶段",
)
async def execute_current_stage(
    pipeline_id: str,
    request: ExecuteStageRequest,
) -> PipelineResponse:
    """执行当前阶段"""
    try:
        pipeline = await _pipeline_service.execute_current_stage(
            pipeline_id=pipeline_id,
            gate_passed=request.gate_passed,
            result_data=request.result_data,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 审批端点
# =============================================================================


@router.post(
    "/pipelines/{pipeline_id}/approve",
    response_model=PipelineResponse,
    summary="批准发布",
    description="在审批阶段批准Agent发布",
)
async def approve_release(
    pipeline_id: str,
    request: ApproveReleaseRequest,
) -> PipelineResponse:
    """批准发布"""
    try:
        pipeline = await _pipeline_service.approve_release(
            pipeline_id=pipeline_id,
            reviewer=request.reviewer,
            notes=request.notes,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/pipelines/{pipeline_id}/reject",
    response_model=PipelineResponse,
    summary="拒绝发布",
    description="在审批阶段拒绝Agent发布",
)
async def reject_release(
    pipeline_id: str,
    request: RejectReleaseRequest,
) -> PipelineResponse:
    """拒绝发布"""
    try:
        pipeline = await _pipeline_service.reject_release(
            pipeline_id=pipeline_id,
            reviewer=request.reviewer,
            reason=request.reason,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 部署端点
# =============================================================================


@router.post(
    "/pipelines/{pipeline_id}/deploy",
    response_model=PipelineResponse,
    summary="部署发布",
    description="在部署阶段执行Agent部署",
)
async def deploy_release(
    pipeline_id: str,
    request: DeployReleaseRequest,
) -> PipelineResponse:
    """部署发布"""
    try:
        pipeline = await _pipeline_service.deploy_release(
            pipeline_id=pipeline_id,
            environment=request.environment,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 回滚端点
# =============================================================================


@router.post(
    "/pipelines/{pipeline_id}/rollback",
    response_model=PipelineResponse,
    summary="回滚发布",
    description="触发流水线回滚",
)
async def rollback_release(
    pipeline_id: str,
    request: RollbackReleaseRequest,
) -> PipelineResponse:
    """回滚发布"""
    try:
        pipeline = await _pipeline_service.rollback_release(
            pipeline_id=pipeline_id,
            reason=request.reason,
            operator=request.operator,
        )
        return _to_pipeline_response(pipeline)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_step_response(step) -> PipelineStepResponse:
    """将步骤实体转换为响应Schema"""
    return PipelineStepResponse(
        id=step.id,
        pipeline_id=step.pipeline_id,
        agent_id=step.agent_id,
        version_id=step.version_id,
        stage=step.stage,
        status=step.status,
        started_at=step.started_at,
        completed_at=step.completed_at,
        error_message=step.error_message,
        result_data=step.result_data,
        gate_passed=step.gate_passed,
        trace_id=step.trace_id,
        duration_ms=step.duration_ms,
        created_at=step.created_at,
        updated_at=step.updated_at,
        tenant_id=step.tenant_id,
    )


def _to_pipeline_response(pipeline) -> PipelineResponse:
    """将流水线实体转换为响应Schema"""
    return PipelineResponse(
        id=pipeline.id,
        agent_id=pipeline.agent_id,
        version_id=pipeline.version_id,
        status=pipeline.status,
        current_stage=pipeline.current_stage,
        steps=[_to_step_response(s) for s in pipeline.steps],
        triggered_by=pipeline.triggered_by,
        progress_percentage=pipeline.progress_percentage,
        total_duration_ms=pipeline.total_duration_ms,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
        tenant_id=pipeline.tenant_id,
    )
