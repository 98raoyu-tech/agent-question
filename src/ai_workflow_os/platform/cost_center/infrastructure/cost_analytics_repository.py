"""
成本分析仓储实现

提供成本预测、聚合和告警实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.cost_aggregation import AggregationTargetType, CostAggregation, PeriodType
from ..domain.cost_alert import AlertTargetType, CostAlert
from ..domain.cost_forecast import CostForecast, TargetType

logger = logging.getLogger(__name__)


class CostAnalyticsRepository:
    """成本分析仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._forecasts: dict[str, CostForecast] = {}
        self._aggregations: dict[str, CostAggregation] = {}
        self._alerts: dict[str, CostAlert] = {}

    # =========================================================================
    # 预测操作
    # =========================================================================

    async def save_forecast(self, forecast: CostForecast) -> CostForecast:
        """保存成本预测

        Args:
            forecast: 成本预测实体

        Returns:
            保存后的预测实体
        """
        self._forecasts[forecast.id] = forecast
        return forecast

    async def find_forecast_by_id(self, forecast_id: str) -> Optional[CostForecast]:
        """根据ID查找预测

        Args:
            forecast_id: 预测标识

        Returns:
            预测实体，未找到返回None
        """
        return self._forecasts.get(forecast_id)

    async def find_latest_forecast(
        self,
        target_id: str,
        target_type: TargetType,
    ) -> Optional[CostForecast]:
        """查找目标的最新预测

        Args:
            target_id: 目标标识
            target_type: 目标类型

        Returns:
            最新的预测实体，未找到返回None
        """
        forecasts = [
            f for f in self._forecasts.values()
            if f.target_id == target_id and f.target_type == target_type
        ]
        if not forecasts:
            return None
        return max(forecasts, key=lambda f: f.generated_at)

    # =========================================================================
    # 聚合操作
    # =========================================================================

    async def save_aggregation(self, aggregation: CostAggregation) -> CostAggregation:
        """保存成本聚合

        Args:
            aggregation: 成本聚合实体

        Returns:
            保存后的聚合实体
        """
        self._aggregations[aggregation.id] = aggregation
        return aggregation

    async def find_aggregations(
        self,
        target_id: str,
        target_type: AggregationTargetType,
        period_type: Optional[PeriodType],
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[CostAggregation]:
        """查询成本聚合记录

        Args:
            target_id: 目标标识
            target_type: 目标类型
            period_type: 周期类型
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        aggregations = [
            a for a in self._aggregations.values()
            if a.target_id == target_id and a.target_type == target_type
        ]

        if period_type is not None:
            aggregations = [a for a in aggregations if a.period_type == period_type]

        aggregations.sort(key=lambda a: a.period_start, reverse=True)

        total = len(aggregations)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = aggregations[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def find_aggregations_by_target(
        self,
        target_id: str,
        target_type: AggregationTargetType,
        period_type: PeriodType,
    ) -> list[CostAggregation]:
        """查找目标的所有聚合记录（不分页）

        Args:
            target_id: 目标标识
            target_type: 目标类型
            period_type: 周期类型

        Returns:
            聚合记录列表
        """
        return [
            a for a in self._aggregations.values()
            if a.target_id == target_id
            and a.target_type == target_type
            and a.period_type == period_type
        ]

    # =========================================================================
    # 告警操作
    # =========================================================================

    async def save_alert(self, alert: CostAlert) -> CostAlert:
        """保存成本告警

        Args:
            alert: 成本告警实体

        Returns:
            保存后的告警实体
        """
        self._alerts[alert.id] = alert
        return alert

    async def find_alert_by_id(self, alert_id: str) -> Optional[CostAlert]:
        """根据ID查找告警

        Args:
            alert_id: 告警标识

        Returns:
            告警实体，未找到返回None
        """
        return self._alerts.get(alert_id)

    async def find_alerts(
        self,
        budget_id: Optional[str],
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[CostAlert]:
        """查询告警列表

        Args:
            budget_id: 预算标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        alerts = list(self._alerts.values())

        if budget_id is not None:
            alerts = [a for a in alerts if a.budget_id == budget_id]

        alerts.sort(key=lambda a: a.triggered_at, reverse=True)

        total = len(alerts)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = alerts[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
