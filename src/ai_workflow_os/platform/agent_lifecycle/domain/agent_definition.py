"""
Agent生命周期定义实体

定义Agent的核心业务实体，包含名称、描述、生命周期状态、版本、所有者、团队、标签和元数据。
支持严格的生命周期状态机转换。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import AgentLifecycleState, VALID_TRANSITIONS


@dataclass
class AgentLifecycleDefinition(BaseEntity):
    """Agent生命周期定义实体

    核心聚合根，描述一个Agent的完整定义及其生命周期状态。

    Attributes:
        name: Agent名称
        description: Agent描述
        lifecycle_state: 当前生命周期状态
        current_version_id: 当前版本标识
        owner_id: 所有者标识
        team_id: 所属团队标识
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    lifecycle_state: AgentLifecycleState = AgentLifecycleState.DRAFT
    current_version_id: Optional[str] = field(default=None)
    owner_id: Optional[str] = field(default=None)
    team_id: Optional[str] = field(default=None)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_transition_to(self, target_state: AgentLifecycleState) -> bool:
        """判断是否可以转换到目标状态

        Args:
            target_state: 目标生命周期状态

        Returns:
            是否允许转换
        """
        allowed_states = VALID_TRANSITIONS.get(self.lifecycle_state, [])
        return target_state in allowed_states

    def transition_to(
        self,
        new_state: AgentLifecycleState,
        operator: Optional[str] = None,
    ) -> None:
        """执行生命周期状态转换

        Args:
            new_state: 目标生命周期状态
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 状态转换不合法
        """
        if not self.can_transition_to(new_state):
            raise BusinessRuleViolationException(
                rule="LIFECYCLE_STATE_TRANSITION",
                message=(
                    f"不允许从 {self.lifecycle_state.value} 转换到 {new_state.value}，"
                    f"允许的目标状态: {[s.value for s in VALID_TRANSITIONS.get(self.lifecycle_state, [])]}"
                ),
            )
        self.lifecycle_state = new_state
        self.touch(operator)
