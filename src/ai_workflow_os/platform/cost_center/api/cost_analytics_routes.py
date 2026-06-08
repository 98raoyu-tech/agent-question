"""
成本分析 FastAPI路由

提供成本查询、预测、聚合和告警管理的RESTful API端点。
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.cost_analytics_service import CostAnalyticsService
from ..domain.cost_aggregation import AggregationTargetType, CostAggregation, PeriodType
from ..domain.cost_alert import AlertSeverity, AlertTargetType, AlertType, CostAlert
from ..domain.cost_forecast import CostForecast, TargetType
from ..infrastructure.cost_analytics_repository import CostAnalyticsRepository
from .cost_analytics_schemas import (
    AggregationListResponse,
    AggregationResponse,
    AlertListResponse,
    AlertResponse,
    CostSummaryResponse,
    CostTrendResponse,
    CreateAlertRequest,
    ForecastResponse,
    GenerateForecastRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cost-analytics", tags=["成本分析"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_cost_analytics_repository = CostAnalyticsRepository()
_cost_analytics_service = CostAnalyticsService(_cost_analytics_repository)


# =========================================================================
# 成本查询端点
# =========================================================================


@router.get(
    "/cost/agent/{agent_id}",
    response_model=CostSummaryResponse,
    summary="查询Agent成本",
    description="查询指定Agent在时间范围内的成本数据",
)
async def get_cost_by_agent(
    agent_id: str,
    period_start: datetime = Query(description="查询起始时间"),
    period_end: datetime = Query(description="查询结束时间"),
) -> CostSummaryResponse:
    """查询Agent成本"""
    try:
        result = await _cost_analytics_service.get_cost_by_agent(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end,
        )
        return CostSummaryResponse(**result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/cost/workflow/{workflow_id}",
    response_model=CostSummaryResponse,
    summary="查询工作流成本",
    description="查询指定工作流在时间范围内的成本数据",
)
async def get_cost_by_workflow(
    workflow_id: str,
    period_start: datetime = Query(description="查询起始时间"),
    period_end: datetime = Query(description="查询结束时间"),
) -> CostSummaryResponse:
    """查询工作流成本"""
    try:
        result = await _cost_analytics_service.get_cost_by_workflow(
            workflow_id=workflow_id,
            period_start=period_start,
            period_end=period_end,
        )
        return CostSummaryResponse(**result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/cost/project/{project_id}",
    response_model=CostSummaryResponse,
    summary="查询项目成本",
    description="查询指定项目在时间范围内的成本数据",
)
async def get_cost_by_project(
    project_id: str,
    period_start: datetime = Query(description="查询起始时间"),
    period_end: datetime = Query(description="查询结束时间"),
) -> CostSummaryResponse:
    """查询项目成本"""
    try:
        result = await _cost_analytics_service.get_cost_by_project(
            project_id=project_id,
            period_start=period_start,
            period_end=period_end,
        )
        return CostSummaryResponse(**result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/cost/tenant/{tenant_id}",
    response_model=CostSummaryResponse,
    summary="查询租户成本",
    description="查询指定租户在时间范围内的成本数据",
)
async def get_cost_by_tenant(
    tenant_id: str,
    period_start: datetime = Query(description="查询起始时间"),
    period_end: datetime = Query(description="查询结束时间"),
) -> CostSummaryResponse:
    """查询租户成本"""
    try:
        result = await _cost_analytics_service.get_cost_by_tenant(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
        )
        return CostSummaryResponse(**result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =========================================================================
# 预测端点
# =========================================================================


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成成本预测",
    description="基于历史数据生成指定目标的成本预测",
)
async def generate_forecast(request: GenerateForecastRequest) -> ForecastResponse:
    """生成成本预测"""
    try:
        forecast = await _cost_analytics_service.generate_forecast(
            target_id=request.target_id,
            target_type=request.target_type,
            period_days=request.forecast_period_days,
        )

        return _to_forecast_response(forecast)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =========================================================================
# 聚合端点
# =========================================================================


@router.get(
    "/aggregations",
    response_model=AggregationListResponse,
    summary="查询成本聚合",
    description="分页查询目标的成本聚合记录",
)
async def list_aggregations(
    target_id: str = Query(description="目标标识"),
    target_type: AggregationTargetType = Query(description="目标类型"),
    period_type: PeriodType = Query(default=None, description="周期类型"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AggregationListResponse:
    """查询成本聚合"""
    try:
        pagination = PaginatedRequest(page=page, page_size=page_size)
        result = await _cost_analytics_service.get_aggregations(
            target_id=target_id,
            target_type=target_type,
            period_type=period_type,
            pagination=pagination,
        )

        return AggregationListResponse(
            items=[_to_aggregation_response(a) for a in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =========================================================================
# 告警端点
# =========================================================================


@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建成本告警",
    description="创建一条成本告警记录",
)
async def create_alert(request: CreateAlertRequest) -> AlertResponse:
    """创建成本告警"""
    try:
        alert = CostAlert(
            budget_id=request.budget_id,
            target_id=request.target_id,
            target_type=request.target_type,
            alert_type=request.alert_type,
            severity=request.severity,
            message=request.message,
            threshold_percentage=request.threshold_percentage,
            current_percentage=request.current_percentage,
            tenant_id=request.tenant_id,
        )

        created_alert = await _cost_analytics_service.create_alert(alert)

        return _to_alert_response(created_alert)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="查询告警列表",
    description="分页查询成本告警列表",
)
async def list_alerts(
    budget_id: str = Query(default=None, description="预算标识"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> AlertListResponse:
    """查询告警列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _cost_analytics_service.list_alerts(budget_id, pagination)

    return AlertListResponse(
        items=[_to_alert_response(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="确认告警",
    description="确认指定的成本告警",
)
async def acknowledge_alert(
    alert_id: str,
    user: str = Query(description="确认者标识"),
) -> AlertResponse:
    """确认告警"""
    try:
        alert = await _cost_analytics_service.acknowledge_alert(
            alert_id=alert_id,
            user=user,
        )

        return _to_alert_response(alert)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =========================================================================
# 趋势端点
# =========================================================================


@router.get(
    "/trends/{target_type}/{target_id}",
    response_model=CostTrendResponse,
    summary="获取成本趋势",
    description="获取指定目标的成本趋势分析数据",
)
async def get_cost_trends(
    target_type: AggregationTargetType,
    target_id: str,
    days: int = Query(default=30, ge=1, le=365, description="分析天数"),
) -> CostTrendResponse:
    """获取成本趋势"""
    try:
        result = await _cost_analytics_service.get_cost_trends(
            target_id=target_id,
            target_type=target_type,
            days=days,
        )

        return CostTrendResponse(**result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =========================================================================
# 响应转换函数
# =========================================================================


def _to_forecast_response(forecast: CostForecast) -> ForecastResponse:
    """将预测实体转换为响应Schema"""
    return ForecastResponse(
        id=forecast.id,
        target_id=forecast.target_id,
        target_type=forecast.target_type,
        forecast_period_days=forecast.forecast_period_days,
        predicted_cost=forecast.predicted_cost,
        confidence_level=forecast.confidence_level,
        trend=forecast.trend,
        historical_avg_daily=forecast.historical_avg_daily,
        forecast_details=forecast.forecast_details,
        generated_at=forecast.generated_at,
        created_at=forecast.created_at,
        updated_at=forecast.updated_at,
        tenant_id=forecast.tenant_id,
    )


def _to_aggregation_response(aggregation: CostAggregation) -> AggregationResponse:
    """将聚合实体转换为响应Schema"""
    return AggregationResponse(
        id=aggregation.id,
        target_id=aggregation.target_id,
        target_type=aggregation.target_type,
        period_type=aggregation.period_type,
        period_start=aggregation.period_start,
        period_end=aggregation.period_end,
        total_cost=aggregation.total_cost,
        breakdown=aggregation.breakdown,
        currency=aggregation.currency,
        record_count=aggregation.record_count,
        created_at=aggregation.created_at,
        updated_at=aggregation.updated_at,
        tenant_id=aggregation.tenant_id,
    )


def _to_alert_response(alert: CostAlert) -> AlertResponse:
    """将告警实体转换为响应Schema"""
    return AlertResponse(
        id=alert.id,
        budget_id=alert.budget_id,
        target_id=alert.target_id,
        target_type=alert.target_type,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        threshold_percentage=alert.threshold_percentage,
        current_percentage=alert.current_percentage,
        triggered_at=alert.triggered_at,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        tenant_id=alert.tenant_id,
    )
