"""
评估门控 FastAPI路由

提供质量门控管理和目标评估的RESTful API端点。
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
from ..application.evaluation_gate_service import EvaluationGateService
from ..domain.enums import EvaluationTargetType
from ..domain.evaluation_report import EvaluationReport
from ..domain.quality_gate import QualityGate
from ..infrastructure.evaluation_gate_repository import EvaluationGateRepository
from .schemas import (
    CreateGateRequest,
    EvaluateTargetRequest,
    GateListResponse,
    GateResponse,
    PublishableResponse,
    ReportListResponse,
    ReportResponse,
    WaiveGateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evaluation-gates", tags=["评估门控"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_evaluation_gate_repository = EvaluationGateRepository()
_evaluation_gate_service = EvaluationGateService(_evaluation_gate_repository)


# =============================================================================
# 门控端点
# =============================================================================


@router.post(
    "/gates",
    response_model=GateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建质量门控",
    description="创建一个新的质量门控",
)
async def create_gate(request: CreateGateRequest) -> GateResponse:
    """创建质量门控

    Args:
        request: 创建门控请求

    Returns:
        创建的门控响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        gate = QualityGate(
            name=request.name,
            description=request.description,
            target_type=request.target_type,
            metrics_thresholds=request.metrics_thresholds,
            is_blocking=request.is_blocking,
            priority=request.priority,
            metadata=request.metadata,
            tenant_id=request.tenant_id,
        )

        created_gate = await _evaluation_gate_service.create_gate(gate)

        return _to_gate_response(created_gate)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/gates",
    response_model=GateListResponse,
    summary="查询门控列表",
    description="分页查询质量门控列表",
)
async def list_gates(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> GateListResponse:
    """查询门控列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识

    Returns:
        门控列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _evaluation_gate_service.list_gates(pagination, tenant_id)

    return GateListResponse(
        items=[_to_gate_response(g) for g in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/gates/{gate_id}",
    response_model=GateResponse,
    summary="获取门控详情",
    description="根据ID获取质量门控的详细信息",
)
async def get_gate(gate_id: str) -> GateResponse:
    """获取门控详情

    Args:
        gate_id: 门控标识

    Returns:
        门控响应

    Raises:
        HTTPException: 门控不存在
    """
    try:
        gate = await _evaluation_gate_service.get_gate(gate_id)
        return _to_gate_response(gate)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/gates/{gate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除门控",
    description="软删除质量门控",
)
async def delete_gate(gate_id: str) -> None:
    """删除门控

    Args:
        gate_id: 门控标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _evaluation_gate_service.delete_gate(gate_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 评估端点
# =============================================================================


@router.post(
    "/evaluate",
    response_model=ReportListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="评估目标",
    description="对目标执行门控评估，返回评估报告列表",
)
async def evaluate_target(request: EvaluateTargetRequest) -> ReportListResponse:
    """评估目标

    Args:
        request: 评估目标请求

    Returns:
        报告列表响应

    Raises:
        HTTPException: 评估失败
    """
    try:
        reports = await _evaluation_gate_service.evaluate_target(
            target_id=request.target_id,
            target_type=request.target_type,
            metric_scores=request.metric_scores,
        )

        return ReportListResponse(
            items=[_to_report_response(r) for r in reports],
            total=len(reports),
        )

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 报告端点
# =============================================================================


@router.get(
    "/reports/target/{target_id}",
    response_model=ReportListResponse,
    summary="获取目标的评估报告",
    description="根据目标标识获取所有评估报告",
)
async def get_reports_by_target(target_id: str) -> ReportListResponse:
    """获取目标的评估报告

    Args:
        target_id: 评估目标标识

    Returns:
        报告列表响应
    """
    reports = await _evaluation_gate_service.get_reports_by_target(target_id)

    return ReportListResponse(
        items=[_to_report_response(r) for r in reports],
        total=len(reports),
    )


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="获取报告详情",
    description="根据ID获取评估报告的详细信息",
)
async def get_report(report_id: str) -> ReportResponse:
    """获取报告详情

    Args:
        report_id: 报告标识

    Returns:
        报告响应

    Raises:
        HTTPException: 报告不存在
    """
    try:
        report = await _evaluation_gate_service.get_report_by_id(report_id)
        return _to_report_response(report)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 豁免端点
# =============================================================================


@router.post(
    "/gates/{gate_id}/waive",
    response_model=GateResponse,
    summary="豁免门控",
    description="豁免指定的质量门控，使其不再阻断发布",
)
async def waive_gate(gate_id: str, request: WaiveGateRequest) -> GateResponse:
    """豁免门控

    Args:
        gate_id: 门控标识
        request: 豁免请求

    Returns:
        更新后的门控响应

    Raises:
        HTTPException: 豁免失败
    """
    try:
        gate = await _evaluation_gate_service.waive_gate(
            gate_id=gate_id,
            operator=request.operator,
            reason=request.reason,
        )

        return _to_gate_response(gate)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 发布检查端点
# =============================================================================


@router.get(
    "/check-publishable/{target_type}/{target_id}",
    response_model=PublishableResponse,
    summary="检查目标是否可发布",
    description="检查目标是否通过所有阻断门控，可以发布",
)
async def check_publishable(
    target_type: EvaluationTargetType,
    target_id: str,
) -> PublishableResponse:
    """检查目标是否可发布

    Args:
        target_type: 评估目标类型
        target_id: 评估目标标识

    Returns:
        发布检查响应
    """
    publishable = await _evaluation_gate_service.check_publishable(
        target_id=target_id,
        target_type=target_type,
    )

    return PublishableResponse(
        target_id=target_id,
        target_type=target_type,
        publishable=publishable,
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_gate_response(gate: QualityGate) -> GateResponse:
    """将门控实体转换为响应Schema

    Args:
        gate: 门控实体

    Returns:
        门控响应
    """
    return GateResponse(
        id=gate.id,
        name=gate.name,
        description=gate.description,
        target_type=gate.target_type,
        gate_status=gate.gate_status,
        metrics_thresholds=gate.metrics_thresholds,
        is_blocking=gate.is_blocking,
        priority=gate.priority,
        metadata=gate.metadata,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        tenant_id=gate.tenant_id,
    )


def _to_report_response(report: EvaluationReport) -> ReportResponse:
    """将评估报告实体转换为响应Schema

    Args:
        report: 评估报告实体

    Returns:
        报告响应
    """
    return ReportResponse(
        id=report.id,
        target_id=report.target_id,
        target_type=report.target_type,
        gate_id=report.gate_id,
        gate_name=report.gate_name,
        status=report.status,
        metric_scores=report.metric_scores,
        overall_score=report.overall_score,
        passed=report.passed,
        evaluated_at=report.evaluated_at,
        evaluator=report.evaluator,
        details=report.details,
        recommendations=report.recommendations,
        created_at=report.created_at,
        updated_at=report.updated_at,
        tenant_id=report.tenant_id,
    )
