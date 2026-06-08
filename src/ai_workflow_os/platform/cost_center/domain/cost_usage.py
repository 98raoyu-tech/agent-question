"""
成本使用记录实体

定义成本使用记录的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import CostType


@dataclass
class CostUsage(BaseEntity):
    """成本使用记录实体

    记录单次资源使用的成本信息。

    Attributes:
        agent_id: 关联的Agent标识
        cost_type: 成本类型
        amount: 成本金额
        currency: 货币单位
        quantity: 使用数量
        unit: 计量单位
        description: 描述
        metadata: 扩展元数据
    """

    agent_id: str = ""
    cost_type: CostType = CostType.LLM_TOKEN
    amount: float = 0.0
    currency: str = "USD"
    quantity: float = 0.0
    unit: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
