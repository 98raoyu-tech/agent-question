"""
SLO实体

定义Agent服务级别目标的核心业务实体，包含目标指标、错误预算和消耗速率监控。
"""

from dataclasses import dataclass, field
from typing import Optional

from ...common.base_entity import BaseEntity


@dataclass
class SLO(BaseEntity):
    """服务级别目标实体

    定义Agent的服务级别目标，追踪单个指标的目标达成情况和错误预算消耗。

    Attributes:
        name: SLO名称
        agent_id: Agent标识
        sla_id: 关联的SLA标识
        metric_name: 指标名称
        target_value: 目标值
        current_value: 当前值
        error_budget_remaining: 剩余错误预算百分比
        burn_rate: 错误预算消耗速率
        period_days: 评估周期（天）
    """

    name: str = ""
    agent_id: str = ""
    sla_id: str = ""
    metric_name: str = ""
    target_value: float = 0.0
    current_value: float = 0.0
    error_budget_remaining: float = 100.0
    burn_rate: float = 0.0
    period_days: int = 30

    def update_current_value(self, value: float, operator: Optional[str] = None) -> None:
        """更新当前值

        Args:
            value: 新的指标值
            operator: 操作者标识
        """
        old_value = self.current_value
        self.current_value = value

        # 更新错误预算
        self.error_budget_remaining = self.calculate_error_budget()

        # 计算消耗速率（简化计算）
        if old_value != 0 and self.target_value != 0:
            self.burn_rate = self._calculate_burn_rate(old_value, value)

        self.touch(operator)

    def calculate_error_budget(self) -> float:
        """计算剩余错误预算

        Returns:
            剩余错误预算百分比（0-100）
        """
        if self.target_value == 0:
            return 100.0

        # 对于"越小越好"的指标（如延迟），target是最大值
        # 对于"越大越好"的指标（如可用性），target是最小值
        if self.metric_name in ("latency", "latency_p99", "error_rate"):
            # 越小越好的指标：错误预算 = (1 - current/target) * 100
            if self.current_value <= self.target_value:
                return 100.0
            if self.target_value == 0:
                return 0.0
            error_ratio = self.current_value / self.target_value
            remaining = max(0.0, (2.0 - error_ratio) * 100.0)
        else:
            # 越大越好的指标（如可用性、成功率）
            if self.current_value >= self.target_value:
                return 100.0
            error_ratio = self.current_value / self.target_value
            remaining = max(0.0, error_ratio * 100.0)

        return round(remaining, 2)

    def is_burning_too_fast(self, threshold: float = 14.4) -> bool:
        """检查错误预算是否消耗过快

        Args:
            threshold: 消耗速率阈值（默认14.4，表示1天消耗2周预算的速率）

        Returns:
            是否消耗过快
        """
        return self.burn_rate > threshold

    def get_remaining_days(self) -> Optional[float]:
        """计算错误预算预计剩余天数

        Returns:
            预计剩余天数，如果消耗速率为0返回None
        """
        if self.burn_rate <= 0:
            return None

        # 剩余天数 = 剩余预算百分比 / 每天消耗百分比
        if self.burn_rate == 0:
            return None

        return round(self.error_budget_remaining / self.burn_rate, 1)

    def _calculate_burn_rate(self, old_value: float, new_value: float) -> float:
        """计算消耗速率

        Args:
            old_value: 旧值
            new_value: 新值

        Returns:
            消耗速率（每天消耗的错误预算百分比）
        """
        if self.target_value == 0:
            return 0.0

        # 简化的消耗速率计算
        # 基于指标值的变化趋势估算
        if self.metric_name in ("latency", "latency_p99", "error_rate"):
            # 越小越好的指标
            if new_value <= self.target_value:
                return 0.0
            overshoot_ratio = (new_value - self.target_value) / self.target_value
            return round(overshoot_ratio * 100.0 / self.period_days, 2)
        else:
            # 越大越好的指标
            if new_value >= self.target_value:
                return 0.0
            undershoot_ratio = (self.target_value - new_value) / self.target_value
            return round(undershoot_ratio * 100.0 / self.period_days, 2)
