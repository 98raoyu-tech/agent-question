"""
策略实体

定义治理策略的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import PolicyStatus, PolicyType


@dataclass
class Policy(BaseEntity):
    """策略实体

    管理平台的治理策略。

    Attributes:
        name: 策略名称
        description: 策略描述
        policy_type: 策略类型
        status: 策略状态
        rules: 策略规则列表
        priority: 优先级（数值越小优先级越高）
        target_agents: 适用的Agent列表（为空表示全局策略）
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    policy_type: PolicyType = PolicyType.ACCESS_CONTROL
    status: PolicyStatus = PolicyStatus.DRAFT
    rules: list[dict[str, Any]] = field(default_factory=list)
    priority: int = 100
    target_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活策略

        Args:
            operator: 操作者标识
        """
        self.status = PolicyStatus.ACTIVE
        self.touch(operator)

    def disable(self, operator: Optional[str] = None) -> None:
        """禁用策略

        Args:
            operator: 操作者标识
        """
        self.status = PolicyStatus.DISABLED
        self.touch(operator)

    def is_applicable(self, agent_id: str) -> bool:
        """判断策略是否适用于指定Agent

        Args:
            agent_id: Agent标识

        Returns:
            是否适用
        """
        if not self.target_agents:
            return True
        return agent_id in self.target_agents
