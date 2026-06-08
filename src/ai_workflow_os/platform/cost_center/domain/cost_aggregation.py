"""
成本聚合实体

定义成本聚合的核心业务实体，支持按不同时间维度和目标类型进行成本汇总。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from .enums import CostType


class AggregationTargetType(str, Enum):
    """聚合目标类型枚举"""

    AGENT = "agent"
    """Agent"""

    WORKFLOW = "workflow"
    """工作流"""

    PROJECT = "project"
    """项目"""

    TENANT = "tenant"
    """租户"""


class PeriodType(str, Enum):
    """聚合周期类型枚举"""

    DAILY = "daily"
    """按日"""

    WEEKLY = "weekly"
    """按周"""

    MONTHLY = "monthly"
    """按月"""

    QUARTERLY = "quarterly"
    """按季度"""

    YEARLY = "yearly"
    """按年"""


@dataclass
class CostAggregation(BaseEntity):
    """成本聚合实体

    按时间维度和目标类型汇总成本数据，提供成本分析的基础数据结构。

    Attributes:
        target_id: 聚合目标标识
        target_type: 聚合目标类型
        period_type: 聚合周期类型
        period_start: 周期开始时间
        period_end: 周期结束时间
        total_cost: 总成本
        breakdown: 按成本类型的分项明细
        currency: 货币单位
        record_count: 记录数量
    """

    target_id: str = ""
    target_type: AggregationTargetType = AggregationTargetType.AGENT
    period_type: PeriodType = PeriodType.DAILY
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    total_cost: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    currency: str = "USD"
    record_count: int = 0

    def add_record(
        self,
        cost_type: CostType,
        amount: float,
        operator: Optional[str] = None,
    ) -> None:
        """添加成本记录到聚合

        累加指定成本类型的金额，并更新总成本和记录数。

        Args:
            cost_type: 成本类型
            amount: 成本金额
            operator: 操作者标识
        """
        type_key = cost_type.value
        current_amount = self.breakdown.get(type_key, 0.0)
        self.breakdown[type_key] = current_amount + amount

        self.total_cost += amount
        self.record_count += 1
        self.touch(operator)

    def get_breakdown(self) -> dict[str, float]:
        """获取成本分项明细

        Returns:
            成本类型到金额的映射字典
        """
        return dict(self.breakdown)
