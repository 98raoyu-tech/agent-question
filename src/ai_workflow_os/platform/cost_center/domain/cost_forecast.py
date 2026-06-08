"""
成本预测实体

定义成本预测的核心业务实体，支持基于历史数据的成本趋势预测。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import ValidationException


class TrendType(str, Enum):
    """趋势类型枚举"""

    INCREASING = "increasing"
    """上升趋势"""

    DECREASING = "decreasing"
    """下降趋势"""

    STABLE = "stable"
    """稳定趋势"""


class TargetType(str, Enum):
    """预测目标类型枚举"""

    AGENT = "agent"
    """Agent"""

    WORKFLOW = "workflow"
    """工作流"""

    PROJECT = "project"
    """项目"""

    TENANT = "tenant"
    """租户"""


@dataclass
class CostForecast(BaseEntity):
    """成本预测实体

    基于历史成本数据进行趋势预测，提供成本预估和预算对比能力。

    Attributes:
        target_id: 预测目标标识
        target_type: 预测目标类型
        forecast_period_days: 预测周期（天）
        predicted_cost: 预测成本
        confidence_level: 置信水平（0-1）
        trend: 趋势类型
        historical_avg_daily: 历史日均成本
        forecast_details: 预测详情（如每日分解）
        generated_at: 预测生成时间
    """

    target_id: str = ""
    target_type: TargetType = TargetType.AGENT
    forecast_period_days: int = 30
    predicted_cost: float = 0.0
    confidence_level: float = 0.0
    trend: TrendType = TrendType.STABLE
    historical_avg_daily: float = 0.0
    forecast_details: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def generate_forecast(
        self,
        historical_data: list[dict[str, Any]],
        operator: Optional[str] = None,
    ) -> None:
        """基于历史数据生成成本预测

        使用历史数据的加权移动平均算法，近期数据权重更高。

        Args:
            historical_data: 历史成本数据列表，每项包含 date 和 amount 字段
            operator: 操作者标识

        Raises:
            ValidationException: 历史数据为空
        """
        if not historical_data:
            raise ValidationException(message="历史数据不能为空，无法生成预测")

        # 按日期排序历史数据
        sorted_data = sorted(historical_data, key=lambda x: x.get("date", ""))

        # 计算日均成本
        total_amount = sum(item.get("amount", 0.0) for item in sorted_data)
        self.historical_avg_daily = total_amount / len(sorted_data)

        # 使用加权移动平均计算预测值
        # 近期数据权重更高：最近的数据权重为 len(sorted_data)，最远的权重为 1
        weighted_sum = 0.0
        weight_total = 0.0
        for index, item in enumerate(sorted_data):
            weight = index + 1
            weighted_sum += item.get("amount", 0.0) * weight
            weight_total += weight

        weighted_avg_daily = weighted_sum / weight_total if weight_total > 0 else 0.0
        self.predicted_cost = weighted_avg_daily * self.forecast_period_days

        # 计算置信水平：基于数据量和波动性
        data_count_factor = min(len(sorted_data) / 30.0, 1.0)
        if len(sorted_data) > 1:
            amounts = [item.get("amount", 0.0) for item in sorted_data]
            mean_amount = sum(amounts) / len(amounts)
            variance = sum((a - mean_amount) ** 2 for a in amounts) / len(amounts)
            cv = (variance ** 0.5) / mean_amount if mean_amount > 0 else 1.0
            stability_factor = max(0.0, 1.0 - cv)
        else:
            stability_factor = 0.5

        self.confidence_level = round(min(data_count_factor * stability_factor, 1.0), 4)

        # 判断趋势
        self._determine_trend(sorted_data)

        # 生成每日分解详情
        self._generate_daily_breakdown(weighted_avg_daily)

        self.generated_at = datetime.now(timezone.utc)
        self.touch(operator)

    def _determine_trend(self, sorted_data: list[dict[str, Any]]) -> None:
        """判断成本趋势

        将数据分为前半段和后半段，通过均值比较确定趋势方向。

        Args:
            sorted_data: 按日期排序的历史数据
        """
        if len(sorted_data) < 2:
            self.trend = TrendType.STABLE
            return

        mid_index = len(sorted_data) // 2
        first_half = sorted_data[:mid_index]
        second_half = sorted_data[mid_index:]

        first_avg = sum(item.get("amount", 0.0) for item in first_half) / len(first_half)
        second_avg = sum(item.get("amount", 0.0) for item in second_half) / len(second_half)

        threshold = 0.05
        if first_avg == 0:
            change_ratio = 1.0 if second_avg > 0 else 0.0
        else:
            change_ratio = (second_avg - first_avg) / first_avg

        if change_ratio > threshold:
            self.trend = TrendType.INCREASING
        elif change_ratio < -threshold:
            self.trend = TrendType.DECREASING
        else:
            self.trend = TrendType.STABLE

    def _generate_daily_breakdown(self, avg_daily_cost: float) -> None:
        """生成每日成本分解

        Args:
            avg_daily_cost: 日均成本
        """
        daily_breakdown = []
        for day in range(1, self.forecast_period_days + 1):
            daily_breakdown.append({
                "day": day,
                "predicted_amount": round(avg_daily_cost, 4),
            })
        self.forecast_details = {"daily_breakdown": daily_breakdown}

    def is_over_budget(self, budget_amount: float) -> bool:
        """判断预测成本是否超出预算

        Args:
            budget_amount: 预算金额

        Returns:
            是否超出预算
        """
        return self.predicted_cost > budget_amount
