"""
成本分析服务

提供成本查询、预测、聚合和告警管理的业务逻辑。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.cost_aggregation import AggregationTargetType, CostAggregation, PeriodType
from ..domain.cost_alert import CostAlert
from ..domain.cost_forecast import CostForecast, TargetType
from ..infrastructure.cost_analytics_repository import CostAnalyticsRepository

logger = logging.getLogger(__name__)


class CostAnalyticsService:
    """成本分析业务服务

    提供成本查询、预测、聚合和告警的完整生命周期管理。

    Attributes:
        repository: 成本分析仓储实例
    """

    def __init__(self, repository: CostAnalyticsRepository) -> None:
        """初始化成本分析服务

        Args:
            repository: 成本分析仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 成本查询
    # =========================================================================

    async def get_cost_by_agent(
        self,
        agent_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """查询Agent的成本数据

        Args:
            agent_id: Agent标识
            period_start: 查询起始时间
            period_end: 查询结束时间

        Returns:
            包含总成本和分项明细的字典
        """
        return await self._get_cost_summary(
            target_id=agent_id,
            target_type=AggregationTargetType.AGENT,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_cost_by_workflow(
        self,
        workflow_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """查询工作流的成本数据

        Args:
            workflow_id: 工作流标识
            period_start: 查询起始时间
            period_end: 查询结束时间

        Returns:
            包含总成本和分项明细的字典
        """
        return await self._get_cost_summary(
            target_id=workflow_id,
            target_type=AggregationTargetType.WORKFLOW,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_cost_by_project(
        self,
        project_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """查询项目的成本数据

        Args:
            project_id: 项目标识
            period_start: 查询起始时间
            period_end: 查询结束时间

        Returns:
            包含总成本和分项明细的字典
        """
        return await self._get_cost_summary(
            target_id=project_id,
            target_type=AggregationTargetType.PROJECT,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_cost_by_tenant(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """查询租户的成本数据

        Args:
            tenant_id: 租户标识
            period_start: 查询起始时间
            period_end: 查询结束时间

        Returns:
            包含总成本和分项明细的字典
        """
        return await self._get_cost_summary(
            target_id=tenant_id,
            target_type=AggregationTargetType.TENANT,
            period_start=period_start,
            period_end=period_end,
        )

    async def _get_cost_summary(
        self,
        target_id: str,
        target_type: AggregationTargetType,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """汇总目标在指定时间段内的成本

        Args:
            target_id: 目标标识
            target_type: 目标类型
            period_start: 起始时间
            period_end: 结束时间

        Returns:
            成本汇总字典
        """
        pagination = PaginatedRequest(page=1, page_size=100)
        result = await self.repository.find_aggregations(
            target_id=target_id,
            target_type=target_type,
            period_type=None,
            pagination=pagination,
        )

        # 按时间范围筛选聚合记录
        filtered = [
            agg for agg in result.items
            if agg.period_start >= period_start and agg.period_end <= period_end
        ]

        total_cost = sum(agg.total_cost for agg in filtered)
        merged_breakdown: dict[str, float] = {}
        for agg in filtered:
            for cost_type, amount in agg.breakdown.items():
                merged_breakdown[cost_type] = merged_breakdown.get(cost_type, 0.0) + amount

        return {
            "target_id": target_id,
            "target_type": target_type.value,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_cost": total_cost,
            "breakdown": merged_breakdown,
            "record_count": len(filtered),
        }

    # =========================================================================
    # 成本预测
    # =========================================================================

    async def generate_forecast(
        self,
        target_id: str,
        target_type: TargetType,
        period_days: int,
        operator: Optional[str] = None,
    ) -> CostForecast:
        """生成成本预测

        基于目标的历史聚合数据，生成未来指定天数的成本预测。

        Args:
            target_id: 目标标识
            target_type: 目标类型
            period_days: 预测天数
            operator: 操作者标识

        Returns:
            生成的预测实体

        Raises:
            ValidationException: 预测天数不合法或缺少历史数据
        """
        if period_days <= 0:
            raise ValidationException(message="预测天数必须大于0")

        # 从聚合记录中提取历史数据
        aggregation_type = AggregationTargetType(target_type.value)
        historical_records = await self.repository.find_aggregations_by_target(
            target_id=target_id,
            target_type=aggregation_type,
            period_type=PeriodType.DAILY,
        )

        historical_data = [
            {"date": record.period_start.isoformat(), "amount": record.total_cost}
            for record in historical_records
        ]

        forecast = CostForecast(
            target_id=target_id,
            target_type=target_type,
            forecast_period_days=period_days,
        )

        forecast.generate_forecast(historical_data, operator)

        saved_forecast = await self.repository.save_forecast(forecast)
        logger.info(
            "成本预测生成成功: target_id=%s, type=%s, predicted_cost=%.2f",
            target_id,
            target_type.value,
            saved_forecast.predicted_cost,
        )

        return saved_forecast

    # =========================================================================
    # 聚合查询
    # =========================================================================

    async def get_aggregations(
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
        return await self.repository.find_aggregations(
            target_id=target_id,
            target_type=target_type,
            period_type=period_type,
            pagination=pagination,
        )

    # =========================================================================
    # 告警管理
    # =========================================================================

    async def create_alert(
        self,
        alert: CostAlert,
        operator: Optional[str] = None,
    ) -> CostAlert:
        """创建成本告警

        Args:
            alert: 告警实体
            operator: 操作者标识

        Returns:
            创建后的告警实体

        Raises:
            ValidationException: 告警消息为空
        """
        if not alert.message or not alert.message.strip():
            raise ValidationException(message="告警消息不能为空")

        alert.created_by = operator
        alert.updated_by = operator

        saved_alert = await self.repository.save_alert(alert)
        logger.info(
            "成本告警创建成功: id=%s, type=%s, severity=%s",
            saved_alert.id,
            saved_alert.alert_type.value,
            saved_alert.severity.value,
        )

        return saved_alert

    async def list_alerts(
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
        return await self.repository.find_alerts(budget_id, pagination)

    async def acknowledge_alert(
        self,
        alert_id: str,
        user: str,
        operator: Optional[str] = None,
    ) -> CostAlert:
        """确认告警

        Args:
            alert_id: 告警标识
            user: 确认者标识
            operator: 操作者标识

        Returns:
            更新后的告警实体

        Raises:
            ResourceNotFoundException: 告警不存在
        """
        alert = await self.repository.find_alert_by_id(alert_id)
        if alert is None:
            raise ResourceNotFoundException(resource_type="告警", resource_id=alert_id)

        alert.acknowledge(user, operator)
        return await self.repository.save_alert(alert)

    # =========================================================================
    # 趋势分析
    # =========================================================================

    async def get_cost_trends(
        self,
        target_id: str,
        target_type: AggregationTargetType,
        days: int,
    ) -> dict[str, Any]:
        """获取成本趋势数据

        基于历史聚合数据计算趋势方向、日均成本和变化率。

        Args:
            target_id: 目标标识
            target_type: 目标类型
            days: 分析天数

        Returns:
            包含趋势信息的字典
        """
        if days <= 0:
            return {
                "target_id": target_id,
                "target_type": target_type.value,
                "days": days,
                "trend": "stable",
                "daily_costs": [],
                "avg_daily_cost": 0.0,
                "total_cost": 0.0,
                "change_rate": 0.0,
            }

        # 获取每日聚合记录
        records = await self.repository.find_aggregations_by_target(
            target_id=target_id,
            target_type=target_type,
            period_type=PeriodType.DAILY,
        )

        # 按时间范围筛选
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = [r for r in records if r.period_start >= cutoff_date]
        filtered.sort(key=lambda r: r.period_start)

        total_cost = sum(r.total_cost for r in filtered)
        avg_daily_cost = total_cost / len(filtered) if filtered else 0.0

        # 计算趋势和变化率
        trend, change_rate = self._calculate_trend(filtered)

        daily_costs = [
            {
                "date": r.period_start.isoformat(),
                "cost": r.total_cost,
                "breakdown": r.get_breakdown(),
            }
            for r in filtered
        ]

        return {
            "target_id": target_id,
            "target_type": target_type.value,
            "days": days,
            "trend": trend,
            "daily_costs": daily_costs,
            "avg_daily_cost": round(avg_daily_cost, 4),
            "total_cost": round(total_cost, 4),
            "change_rate": round(change_rate, 4),
        }

    def _calculate_trend(
        self,
        records: list[CostAggregation],
    ) -> tuple[str, float]:
        """计算成本趋势和变化率

        将数据分为前半段和后半段，比较均值确定趋势。

        Args:
            records: 按时间排序的聚合记录

        Returns:
            (趋势方向, 变化率) 元组
        """
        if len(records) < 2:
            return "stable", 0.0

        mid_index = len(records) // 2
        first_half = records[:mid_index]
        second_half = records[mid_index:]

        first_avg = sum(r.total_cost for r in first_half) / len(first_half)
        second_avg = sum(r.total_cost for r in second_half) / len(second_half)

        if first_avg == 0:
            change_rate = 1.0 if second_avg > 0 else 0.0
        else:
            change_rate = (second_avg - first_avg) / first_avg

        threshold = 0.05
        if change_rate > threshold:
            trend = "increasing"
        elif change_rate < -threshold:
            trend = "decreasing"
        else:
            trend = "stable"

        return trend, change_rate
