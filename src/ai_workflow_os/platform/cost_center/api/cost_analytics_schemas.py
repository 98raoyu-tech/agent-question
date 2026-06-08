"""
成本分析请求/响应Schema

定义成本分析相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.cost_aggregation import AggregationTargetType, PeriodType
from ..domain.cost_alert import AlertSeverity, AlertTargetType, AlertType
from ..domain.cost_forecast import TargetType, TrendType


# =============================================================================
# 成本查询Schema
# =============================================================================


class CostSummaryResponse(BaseModel):
    """成本汇总响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    period_start: str = Field(description="查询起始时间")
    period_end: str = Field(description="查询结束时间")
    total_cost: float = Field(description="总成本")
    breakdown: dict[str, float] = Field(description="成本分项明细")
    record_count: int = Field(description="记录数量")


# =============================================================================
# 预测Schema
# =============================================================================


class GenerateForecastRequest(CreateDTO):
    """生成预测请求"""

    target_id: str = Field(description="预测目标标识")
    target_type: TargetType = Field(description="预测目标类型")
    forecast_period_days: int = Field(gt=0, le=365, description="预测周期（天）")


class ForecastResponse(BaseDTO):
    """预测响应"""

    target_id: str = Field(description="预测目标标识")
    target_type: TargetType = Field(description="预测目标类型")
    forecast_period_days: int = Field(description="预测周期（天）")
    predicted_cost: float = Field(description="预测成本")
    confidence_level: float = Field(description="置信水平（0-1）")
    trend: TrendType = Field(description="趋势类型")
    historical_avg_daily: float = Field(description="历史日均成本")
    forecast_details: dict[str, Any] = Field(description="预测详情")
    generated_at: datetime = Field(description="预测生成时间")


# =============================================================================
# 聚合Schema
# =============================================================================


class AggregationResponse(BaseDTO):
    """聚合响应"""

    target_id: str = Field(description="聚合目标标识")
    target_type: AggregationTargetType = Field(description="聚合目标类型")
    period_type: PeriodType = Field(description="聚合周期类型")
    period_start: datetime = Field(description="周期开始时间")
    period_end: datetime = Field(description="周期结束时间")
    total_cost: float = Field(description="总成本")
    breakdown: dict[str, float] = Field(description="成本分项明细")
    currency: str = Field(description="货币单位")
    record_count: int = Field(description="记录数量")


class AggregationListResponse(BaseModel):
    """聚合列表响应"""

    items: list[AggregationResponse] = Field(description="聚合列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 告警Schema
# =============================================================================


class CreateAlertRequest(CreateDTO):
    """创建告警请求"""

    budget_id: str = Field(description="关联的预算标识")
    target_id: str = Field(description="告警目标标识")
    target_type: AlertTargetType = Field(description="告警目标类型")
    alert_type: AlertType = Field(description="告警类型")
    severity: AlertSeverity = Field(description="告警严重级别")
    message: str = Field(min_length=1, description="告警消息")
    threshold_percentage: float = Field(ge=0, le=100, description="阈值百分比")
    current_percentage: float = Field(ge=0, description="当前百分比")


class AlertResponse(BaseDTO):
    """告警响应"""

    budget_id: str = Field(description="关联的预算标识")
    target_id: str = Field(description="告警目标标识")
    target_type: AlertTargetType = Field(description="告警目标类型")
    alert_type: AlertType = Field(description="告警类型")
    severity: AlertSeverity = Field(description="告警严重级别")
    message: str = Field(description="告警消息")
    threshold_percentage: float = Field(description="阈值百分比")
    current_percentage: float = Field(description="当前百分比")
    triggered_at: datetime = Field(description="告警触发时间")
    acknowledged: bool = Field(description="是否已确认")
    acknowledged_by: Optional[str] = Field(default=None, description="确认者标识")


class AlertListResponse(BaseModel):
    """告警列表响应"""

    items: list[AlertResponse] = Field(description="告警列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 趋势Schema
# =============================================================================


class CostTrendResponse(BaseModel):
    """成本趋势响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    days: int = Field(description="分析天数")
    trend: str = Field(description="趋势方向")
    daily_costs: list[dict[str, Any]] = Field(description="每日成本数据")
    avg_daily_cost: float = Field(description="日均成本")
    total_cost: float = Field(description="总成本")
    change_rate: float = Field(description="变化率")
