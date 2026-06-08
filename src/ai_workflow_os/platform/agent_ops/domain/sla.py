"""
SLA实体

定义Agent服务级别协议的核心业务实体，包含目标指标、当前指标和合规性检查。
"""

from dataclasses import dataclass, field
from typing import Optional

from ...common.base_entity import BaseEntity


@dataclass
class SLA(BaseEntity):
    """服务级别协议实体

    定义Agent的服务级别协议，监控关键指标的达成情况。

    Attributes:
        name: SLA名称
        agent_id: Agent标识
        target_uptime: 目标正常运行时间百分比
        target_latency_p99_ms: 目标P99延迟（毫秒）
        target_success_rate: 目标成功率百分比
        target_availability: 目标可用性百分比
        period_days: 评估周期（天）
        current_uptime: 当前正常运行时间百分比
        current_latency_p99: 当前P99延迟（毫秒）
        current_success_rate: 当前成功率百分比
        current_availability: 当前可用性百分比
        is_met: 是否满足SLA
    """

    name: str = ""
    agent_id: str = ""
    target_uptime: float = 99.9
    target_latency_p99_ms: float = 500.0
    target_success_rate: float = 99.5
    target_availability: float = 99.99
    period_days: int = 30
    current_uptime: float = 0.0
    current_latency_p99: float = 0.0
    current_success_rate: float = 0.0
    current_availability: float = 0.0
    is_met: bool = False

    def update_metrics(
        self,
        uptime: float,
        latency: float,
        success_rate: float,
        availability: float,
        operator: Optional[str] = None,
    ) -> None:
        """更新当前指标

        Args:
            uptime: 正常运行时间百分比（0-100）
            latency: P99延迟（毫秒）
            success_rate: 成功率百分比（0-100）
            availability: 可用性百分比（0-100）
            operator: 操作者标识
        """
        self.current_uptime = uptime
        self.current_latency_p99 = latency
        self.current_success_rate = success_rate
        self.current_availability = availability
        self.is_met = self.check_compliance()
        self.touch(operator)

    def check_compliance(self) -> bool:
        """检查是否满足SLA

        Returns:
            是否满足所有目标指标
        """
        # 检查各项指标是否达标
        uptime_met = self.current_uptime >= self.target_uptime
        latency_met = self.current_latency_p99 <= self.target_latency_p99_ms
        success_met = self.current_success_rate >= self.target_success_rate
        availability_met = self.current_availability >= self.target_availability

        return all([uptime_met, latency_met, success_met, availability_met])

    def get_compliance_details(self) -> dict[str, dict[str, float | bool]]:
        """获取合规性详情

        Returns:
            各项指标的合规情况
        """
        return {
            "uptime": {
                "target": self.target_uptime,
                "current": self.current_uptime,
                "met": self.current_uptime >= self.target_uptime,
            },
            "latency_p99": {
                "target": self.target_latency_p99_ms,
                "current": self.current_latency_p99,
                "met": self.current_latency_p99 <= self.target_latency_p99_ms,
            },
            "success_rate": {
                "target": self.target_success_rate,
                "current": self.current_success_rate,
                "met": self.current_success_rate >= self.target_success_rate,
            },
            "availability": {
                "target": self.target_availability,
                "current": self.current_availability,
                "met": self.current_availability >= self.target_availability,
            },
        }

    def get_error_budget(self) -> float:
        """计算错误预算（剩余百分比）

        Returns:
            剩余错误预算百分比（0-100）
        """
        if self.target_availability == 0:
            return 100.0

        # 错误预算 = 100% - 目标不可用性
        target_error = 100.0 - self.target_availability
        current_error = 100.0 - self.current_availability

        if target_error == 0:
            return 100.0 if current_error <= 0 else 0.0

        # 剩余错误预算百分比
        remaining = max(0.0, (1.0 - current_error / target_error) * 100.0)
        return round(remaining, 2)
