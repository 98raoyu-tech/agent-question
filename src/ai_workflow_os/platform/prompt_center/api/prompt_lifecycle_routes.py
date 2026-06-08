"""
Prompt生命周期 FastAPI路由

提供Prompt实验、基准测试、审批、发布和回滚的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ..application.prompt_lifecycle_service import PromptLifecycleService
from ..domain.prompt_approval import PromptApproval
from ..domain.prompt_benchmark import PromptBenchmark
from ..domain.prompt_experiment import PromptExperiment
from ..domain.prompt_release import PromptRelease
from ..domain.prompt_rollback import PromptRollback
from ..infrastructure.prompt_lifecycle_repository import PromptLifecycleRepository
from .prompt_lifecycle_schemas import (
    ApprovalListResponse,
    ApprovalResponse,
    ApproveVersionRequest,
    BenchmarkListResponse,
    BenchmarkResponse,
    CompleteExperimentRequest,
    CreateExperimentRequest,
    ExperimentListResponse,
    ExperimentResponse,
    RejectVersionRequest,
    ReleaseListResponse,
    ReleaseResponse,
    ReleaseVersionRequest,
    RollbackReleaseRequest,
    RollbackResponse,
    RunBenchmarkRequest,
    StartExperimentRequest,
    SubmitApprovalRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prompt-lifecycle", tags=["Prompt生命周期"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_lifecycle_repository = PromptLifecycleRepository()
_lifecycle_service = PromptLifecycleService(_lifecycle_repository)


# =============================================================================
# 实验相关端点
# =============================================================================


@router.post(
    "/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建实验",
    description="创建一个新的Prompt A/B测试实验",
)
async def create_experiment(request: CreateExperimentRequest) -> ExperimentResponse:
    """创建实验"""
    try:
        experiment = await _lifecycle_service.create_experiment(
            prompt_id=request.prompt_id,
            variant_a_id=request.variant_a_version_id,
            variant_b_id=request.variant_b_version_id,
            traffic_split=request.traffic_split,
            experiment_name=request.experiment_name,
            sample_size=request.sample_size,
            operator=request.tenant_id,
        )

        return _to_experiment_response(experiment)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/experiments/{experiment_id}/start",
    response_model=ExperimentResponse,
    summary="启动实验",
    description="启动指定的实验",
)
async def start_experiment(
    experiment_id: str,
    request: StartExperimentRequest,
) -> ExperimentResponse:
    """启动实验"""
    try:
        experiment = await _lifecycle_service.start_experiment(
            experiment_id=experiment_id,
            operator=request.operator,
        )

        return _to_experiment_response(experiment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/experiments/{experiment_id}/complete",
    response_model=ExperimentResponse,
    summary="完成实验",
    description="完成指定的实验并记录获胜版本",
)
async def complete_experiment(
    experiment_id: str,
    request: CompleteExperimentRequest,
) -> ExperimentResponse:
    """完成实验"""
    try:
        experiment = await _lifecycle_service.complete_experiment(
            experiment_id=experiment_id,
            winner_id=request.winner_version_id,
            operator=request.operator,
        )

        return _to_experiment_response(experiment)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/prompts/{prompt_id}/experiments",
    response_model=ExperimentListResponse,
    summary="获取Prompt的实验列表",
    description="获取指定Prompt模板的所有实验",
)
async def list_experiments(prompt_id: str) -> ExperimentListResponse:
    """获取Prompt的实验列表"""
    experiments = await _lifecycle_service.get_experiments(prompt_id)

    return ExperimentListResponse(
        items=[_to_experiment_response(e) for e in experiments],
    )


# =============================================================================
# 基准测试相关端点
# =============================================================================


@router.post(
    "/benchmarks",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="运行基准测试",
    description="创建并运行Prompt版本的基准测试",
)
async def run_benchmark(request: RunBenchmarkRequest) -> BenchmarkResponse:
    """运行基准测试"""
    try:
        benchmark = await _lifecycle_service.run_benchmark(
            prompt_id=request.prompt_id,
            version_id=request.version_id,
            benchmark_name=request.benchmark_name,
            test_cases=request.test_cases,
            operator=request.tenant_id,
        )

        return _to_benchmark_response(benchmark)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/prompts/{prompt_id}/benchmarks",
    response_model=BenchmarkListResponse,
    summary="获取Prompt的基准测试列表",
    description="获取指定Prompt模板的所有基准测试",
)
async def list_benchmarks(prompt_id: str) -> BenchmarkListResponse:
    """获取Prompt的基准测试列表"""
    benchmarks = await _lifecycle_service.get_benchmarks(prompt_id)

    return BenchmarkListResponse(
        items=[_to_benchmark_response(b) for b in benchmarks],
    )


# =============================================================================
# 审批相关端点
# =============================================================================


@router.post(
    "/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交审批",
    description="提交Prompt版本的审批申请",
)
async def submit_approval(request: SubmitApprovalRequest) -> ApprovalResponse:
    """提交审批"""
    try:
        approval = await _lifecycle_service.submit_approval(
            prompt_id=request.prompt_id,
            version_id=request.version_id,
            operator=request.tenant_id,
        )

        return _to_approval_response(approval)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.put(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
    summary="批准版本",
    description="批准指定的审批申请",
)
async def approve_version(
    approval_id: str,
    request: ApproveVersionRequest,
) -> ApprovalResponse:
    """批准版本"""
    try:
        approval = await _lifecycle_service.approve_version(
            approval_id=approval_id,
            approver=request.approver,
            notes=request.notes,
            operator=request.operator,
        )

        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.put(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalResponse,
    summary="拒绝版本",
    description="拒绝指定的审批申请",
)
async def reject_version(
    approval_id: str,
    request: RejectVersionRequest,
) -> ApprovalResponse:
    """拒绝版本"""
    try:
        approval = await _lifecycle_service.reject_version(
            approval_id=approval_id,
            approver=request.approver,
            reason=request.reason,
            operator=request.operator,
        )

        return _to_approval_response(approval)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/prompts/{prompt_id}/approvals",
    response_model=ApprovalListResponse,
    summary="获取Prompt的审批列表",
    description="获取指定Prompt模板的所有审批",
)
async def list_approvals(prompt_id: str) -> ApprovalListResponse:
    """获取Prompt的审批列表"""
    approvals = await _lifecycle_service.get_approvals(prompt_id)

    return ApprovalListResponse(
        items=[_to_approval_response(a) for a in approvals],
    )


# =============================================================================
# 发布相关端点
# =============================================================================


@router.post(
    "/releases",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发布版本",
    description="发布Prompt版本到指定环境",
)
async def release_version(request: ReleaseVersionRequest) -> ReleaseResponse:
    """发布版本"""
    try:
        release = await _lifecycle_service.release_version(
            prompt_id=request.prompt_id,
            version_id=request.version_id,
            release_name=request.release_name,
            environment=request.environment,
            release_notes=request.release_notes,
            operator=request.tenant_id,
        )

        return _to_release_response(release)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/releases/{release_id}/rollback",
    response_model=RollbackResponse,
    summary="回滚发布",
    description="回滚指定的发布到目标版本",
)
async def rollback_release(
    release_id: str,
    request: RollbackReleaseRequest,
) -> RollbackResponse:
    """回滚发布"""
    try:
        rollback = await _lifecycle_service.rollback_release(
            release_id=release_id,
            to_version_id=request.to_version_id,
            reason=request.reason,
            operator=request.operator,
        )

        return _to_rollback_response(rollback)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/prompts/{prompt_id}/releases",
    response_model=ReleaseListResponse,
    summary="获取Prompt的发布列表",
    description="获取指定Prompt模板的所有发布",
)
async def list_releases(prompt_id: str) -> ReleaseListResponse:
    """获取Prompt的发布列表"""
    releases = await _lifecycle_service.get_releases(prompt_id)

    return ReleaseListResponse(
        items=[_to_release_response(r) for r in releases],
    )


# =============================================================================
# 转换函数
# =============================================================================


def _to_experiment_response(experiment: PromptExperiment) -> ExperimentResponse:
    """将实验实体转换为响应Schema"""
    return ExperimentResponse(
        id=experiment.id,
        prompt_id=experiment.prompt_id,
        experiment_name=experiment.experiment_name,
        variant_a_version_id=experiment.variant_a_version_id,
        variant_b_version_id=experiment.variant_b_version_id,
        status=experiment.status,
        traffic_split=experiment.traffic_split,
        sample_size=experiment.sample_size,
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
        results=experiment.results,
        winner_version_id=experiment.winner_version_id,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        tenant_id=experiment.tenant_id,
    )


def _to_benchmark_response(benchmark: PromptBenchmark) -> BenchmarkResponse:
    """将基准测试实体转换为响应Schema"""
    return BenchmarkResponse(
        id=benchmark.id,
        prompt_id=benchmark.prompt_id,
        version_id=benchmark.version_id,
        benchmark_name=benchmark.benchmark_name,
        test_cases=benchmark.test_cases,
        status=benchmark.status,
        avg_score=benchmark.avg_score,
        avg_latency_ms=benchmark.avg_latency_ms,
        avg_cost=benchmark.avg_cost,
        total_tokens=benchmark.total_tokens,
        results=benchmark.results,
        completed_at=benchmark.completed_at,
        created_at=benchmark.created_at,
        updated_at=benchmark.updated_at,
        tenant_id=benchmark.tenant_id,
    )


def _to_approval_response(approval: PromptApproval) -> ApprovalResponse:
    """将审批实体转换为响应Schema"""
    return ApprovalResponse(
        id=approval.id,
        prompt_id=approval.prompt_id,
        version_id=approval.version_id,
        requested_by=approval.requested_by,
        approved_by=approval.approved_by,
        status=approval.status,
        requested_at=approval.requested_at,
        approved_at=approval.approved_at,
        approval_notes=approval.approval_notes,
        rejection_reason=approval.rejection_reason,
        criteria=approval.criteria,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
        tenant_id=approval.tenant_id,
    )


def _to_release_response(release: PromptRelease) -> ReleaseResponse:
    """将发布实体转换为响应Schema"""
    return ReleaseResponse(
        id=release.id,
        prompt_id=release.prompt_id,
        version_id=release.version_id,
        release_name=release.release_name,
        release_notes=release.release_notes,
        status=release.status,
        deployed_at=release.deployed_at,
        rolled_back_at=release.rolled_back_at,
        traffic_percentage=release.traffic_percentage,
        environment=release.environment,
        created_at=release.created_at,
        updated_at=release.updated_at,
        tenant_id=release.tenant_id,
    )


def _to_rollback_response(rollback: PromptRollback) -> RollbackResponse:
    """将回滚实体转换为响应Schema"""
    return RollbackResponse(
        id=rollback.id,
        prompt_id=rollback.prompt_id,
        from_version_id=rollback.from_version_id,
        to_version_id=rollback.to_version_id,
        reason=rollback.reason,
        status=rollback.status,
        initiated_by=rollback.initiated_by,
        completed_at=rollback.completed_at,
        created_at=rollback.created_at,
        updated_at=rollback.updated_at,
        tenant_id=rollback.tenant_id,
    )
