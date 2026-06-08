"""
预算实体

定义预算管理的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import BudgetStatus


@dataclass
class CostBudget(BaseEntity):
    """预算实体

    管理Agent或租户的成本预算。

    Attributes:
        name: 预算名称
        agent_id: 关联的Agent标识（为空表示租户级预算）
        budget_amount: 预算金额
        used_amount: 已使用金额
        currency: 货币单位
        status: 预算状态
        period: 预算周期（daily/weekly/monthly）
        alert_threshold: 告警阈值百分比
        metadata: 扩展元数据
    """

    name: str = ""
    agent_id: str = ""
    budget_amount: float = 0.0
    used_amount: float = 0.0
    currency: str = "USD"
    status: BudgetStatus = BudgetStatus.ACTIVE
    period: str = "monthly"
    alert_threshold: float = 80.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_amount(self) -> float:
        """计算剩余预算

        Returns:
            剩余预算金额
        """
        return max(0.0, self.budget_amount - self.used_amount)

    @property
    def usage_percentage(self) -> float:
        """计算使用百分比

        Returns:
            使用百分比（0-100）
        """
        if self.budget_amount <= 0:
            return 0.0
        return (self.used_amount / self.budget_amount) * 100

    @property
    def is_exceeded(self) -> bool:
        """判断是否已超出预算

        Returns:
            是否已超出
        """
        return self.used_amount >= self.budget_amount

    @property
    def is_alert_needed(self) -> bool:
        """判断是否需要告警

        Returns:
            是否需要告警
        """
        return self.usage_percentage >= self.alert_threshold

    def add_usage(self, amount: float, operator: Optional[str] = None) -> None:
        """添加使用量

        Args:
            amount: 使用金额
            operator: 操作者标识
        """
        self.used_amount += amount
        if self.is_exceeded:
            self.status = BudgetStatus.EXCEEDED
        self.touch(operator)

    def reset(self, operator: Optional[str] = None) -> None:
        """重置使用量

        Args:
            operator: 操作者标识
        """
        self.used_amount = 0.0
        self.status = BudgetStatus.ACTIVE
        self.touch(operator)

    def suspend(self, operator: Optional[str] = None) -> None:
        """暂停预算

        Args:
            operator: 操作者标识
        """
        self.status = BudgetStatus.SUSPENDED
        self.touch(operator)
