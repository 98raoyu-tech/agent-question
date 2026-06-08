"""
成本配额实体

定义成本配额管理的核心业务实体，支持配额消耗、重置和使用率计算。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import QuotaStatus


@dataclass
class CostQuota(BaseEntity):
    """成本配额实体

    管理Agent或项目的成本配额，支持消耗追踪、余额计算和配额重置。

    Attributes:
        name: 配额名称
        agent_id: 关联的Agent标识
        project_id: 关联的项目标识
        quota_amount: 配额总额
        used_amount: 已使用金额
        currency: 货币单位
        period: 配额周期（daily/weekly/monthly）
        status: 配额状态
        metadata: 扩展元数据
    """

    name: str = ""
    agent_id: str = ""
    project_id: str = ""
    quota_amount: float = 0.0
    used_amount: float = 0.0
    currency: str = "USD"
    period: str = "monthly"
    status: QuotaStatus = QuotaStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def remaining(self) -> float:
        """计算剩余配额

        Returns:
            剩余配额金额
        """
        return max(0.0, self.quota_amount - self.used_amount)

    @property
    def usage_percentage(self) -> float:
        """计算使用百分比

        Returns:
            使用百分比（0-100）
        """
        if self.quota_amount <= 0:
            return 0.0
        return (self.used_amount / self.quota_amount) * 100

    @property
    def is_exceeded(self) -> bool:
        """判断是否已超出配额

        Returns:
            是否已超出
        """
        return self.used_amount >= self.quota_amount

    def consume(
        self,
        amount: float,
        operator: Optional[str] = None,
    ) -> None:
        """消耗配额

        Args:
            amount: 消耗金额
            operator: 操作者标识

        Raises:
            ValueError: 消耗金额必须为正数
        """
        if amount <= 0:
            raise ValueError("消耗金额必须为正数")

        self.used_amount += amount
        if self.is_exceeded:
            self.status = QuotaStatus.EXCEEDED
        self.touch(operator)

    def reset(self, operator: Optional[str] = None) -> None:
        """重置配额使用量

        Args:
            operator: 操作者标识
        """
        self.used_amount = 0.0
        self.status = QuotaStatus.ACTIVE
        self.touch(operator)
