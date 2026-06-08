"""
评估中心 FastAPI路由

提供评测数据集和运行管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.evaluation_service import EvaluationService
from ..domain.evaluation_dataset import EvaluationDataset
from ..domain.evaluation_run import EvaluationRun
from ..infrastructure.evaluation_repository import EvaluationRepository
from .schemas import (
    CreateDatasetRequest,
    CreateRunRequest,
    DatasetListResponse,
    DatasetResponse,
    RunListResponse,
    RunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evaluation-center", tags=["评估中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_evaluation_repository = EvaluationRepository()
_evaluation_service = EvaluationService(_evaluation_repository)


# =============================================================================
# 数据集端点
# =============================================================================


@router.post(
    "/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建评测数据集",
    description="创建一个新的评测数据集",
)
async def create_dataset(request: CreateDatasetRequest) -> DatasetResponse:
    """创建评测数据集

    Args:
        request: 创建数据集请求

    Returns:
        创建的数据集响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        dataset = EvaluationDataset(
            name=request.name,
            description=request.description,
            agent_id=request.agent_id,
            test_cases=request.test_cases,
            metrics=request.metrics,
            tags=request.tags,
            tenant_id=request.tenant_id,
        )

        created_dataset = await _evaluation_service.create_dataset(dataset)

        return _to_dataset_response(created_dataset)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="获取数据集详情",
    description="根据ID获取评测数据集的详细信息",
)
async def get_dataset(dataset_id: str) -> DatasetResponse:
    """获取数据集详情

    Args:
        dataset_id: 数据集标识

    Returns:
        数据集响应

    Raises:
        HTTPException: 数据集不存在
    """
    try:
        dataset = await _evaluation_service.get_dataset(dataset_id)
        return _to_dataset_response(dataset)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/datasets",
    response_model=DatasetListResponse,
    summary="查询数据集列表",
    description="分页查询评测数据集列表",
)
async def list_datasets(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> DatasetListResponse:
    """查询数据集列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识

    Returns:
        数据集列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _evaluation_service.list_datasets(pagination, tenant_id)

    return DatasetListResponse(
        items=[_to_dataset_response(d) for d in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.delete(
    "/datasets/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除数据集",
    description="软删除评测数据集",
)
async def delete_dataset(dataset_id: str) -> None:
    """删除数据集

    Args:
        dataset_id: 数据集标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _evaluation_service.delete_dataset(dataset_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 运行端点
# =============================================================================


@router.post(
    "/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建评测运行",
    description="创建一个新的评测运行",
)
async def create_run(request: CreateRunRequest) -> RunResponse:
    """创建评测运行

    Args:
        request: 创建运行请求

    Returns:
        创建的运行响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        run = EvaluationRun(
            dataset_id=request.dataset_id,
            agent_id=request.agent_id,
            run_name=request.run_name,
            config=request.config,
            tenant_id=request.tenant_id,
        )

        created_run = await _evaluation_service.create_run(run)

        return _to_run_response(created_run)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/runs/{run_id}",
    response_model=RunResponse,
    summary="获取运行详情",
    description="根据ID获取评测运行的详细信息",
)
async def get_run(run_id: str) -> RunResponse:
    """获取运行详情

    Args:
        run_id: 运行标识

    Returns:
        运行响应

    Raises:
        HTTPException: 运行不存在
    """
    try:
        run = await _evaluation_service.get_run(run_id)
        return _to_run_response(run)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/runs",
    response_model=RunListResponse,
    summary="查询运行列表",
    description="分页查询评测运行列表",
)
async def list_runs(
    dataset_id: Optional[str] = Query(default=None, description="数据集标识"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> RunListResponse:
    """查询运行列表

    Args:
        dataset_id: 数据集标识
        page: 页码
        page_size: 每页大小

    Returns:
        运行列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _evaluation_service.list_runs(dataset_id, pagination)

    return RunListResponse(
        items=[_to_run_response(r) for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_dataset_response(dataset: EvaluationDataset) -> DatasetResponse:
    """将数据集实体转换为响应Schema

    Args:
        dataset: 数据集实体

    Returns:
        数据集响应
    """
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        agent_id=dataset.agent_id,
        test_cases=dataset.test_cases,
        metrics=dataset.metrics,
        tags=dataset.tags,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        tenant_id=dataset.tenant_id,
    )


def _to_run_response(run: EvaluationRun) -> RunResponse:
    """将运行实体转换为响应Schema

    Args:
        run: 运行实体

    Returns:
        运行响应
    """
    return RunResponse(
        id=run.id,
        dataset_id=run.dataset_id,
        agent_id=run.agent_id,
        run_name=run.run_name,
        status=run.status,
        total_cases=run.total_cases,
        completed_cases=run.completed_cases,
        failed_cases=run.failed_cases,
        progress=run.progress,
        success_rate=run.success_rate,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
        tenant_id=run.tenant_id,
    )
