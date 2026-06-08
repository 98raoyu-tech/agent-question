"""
工具使用分析实体

统计工具的调用量、成功率和延迟等指标。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ...common.base_entity import BaseEntity


@dataclass
class ToolUsageAnalytics(BaseEntity):
    """工具使用分析实体

    按周期聚合工具的使用统计数据。

    Attributes:
        tool_id: 关联的工具标识
        total_calls: 总调用次数
        success_count: 成功次数
        failure_count: 失败次数
        avg_latency_ms: 平均延迟（毫秒）
        total_cost: 累计费用
        last_used_at: 最后使用时间
        period_start: 统计周期开始时间
        period_end: 统计周期结束时间
        top_consumers: 主要调用方列表
    """

    tool_id: str = ""
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    total_cost: float = 0.0
    last_used_at: Optional[datetime] = field(default=None)
    period_start: Optional[datetime] = field(default=None)
    period_end: Optional[datetime] = field(default=None)
    top_consumers: list[dict] = field(default_factory=list)

    def record_call(
        self,
        success: bool,
        latency_ms: float,
        cost: float = 0.0,
        operator: Optional[str] = None,
    ) -> None:
        """记录一次调用

        Args:
            success: 是否成功
            latency_ms: 本次延迟（毫秒）
            cost: 本次费用
            operator: 操作者标识
        """
        total_latency = self.avg_latency_ms * self.total_calls + latency_ms
        self.total_calls += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.avg_latency_ms = total_latency / self.total_calls
        self.total_cost += cost
        self.last_used_at = datetime.utcnow()
        self.touch(operator)

    def get_success_rate(self) -> float:
        """获取成功率

        Returns:
            成功率百分比，无调用记录时返回0.0
        """
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls
