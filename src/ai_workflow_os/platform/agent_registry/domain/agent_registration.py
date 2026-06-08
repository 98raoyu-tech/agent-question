"""
Agent注册实体

定义Agent注册的核心业务实体，包含Agent的基本信息、状态管理和元数据。
"""

from dataclasses import dataclass, field
from typing import Any

from ...common.base_entity import BaseEntity
from .enums import AgentRegistryStatus, FrameworkType, HealthStatus


@dataclass
class AgentRegistration(BaseEntity):
    """Agent注册实体

    核心聚合根，描述一个已注册Agent的完整信息，包括名称、版本、框架、
    所属团队、端点、状态、标签和能力等。

    Attributes:
        name: Agent名称
        description: Agent描述
        version: Agent版本号
        framework: Agent使用的框架类型
        model_name: Agent使用的模型名称
        owner_id: 所有者标识
        team_id: 所属团队标识
        endpoint: Agent服务端点（可选）
        status: Agent注册状态
        health_status: Agent健康状态
        tags: 标签列表
        metadata: 扩展元数据
        capabilities: 能力列表
    """

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    framework: FrameworkType = FrameworkType.CUSTOM
    model_name: str = ""
    owner_id: str = ""
    team_id: str = ""
    endpoint: str | None = None
    status: AgentRegistryStatus = AgentRegistryStatus.REGISTERED
    health_status: HealthStatus = HealthStatus.UNKNOWN
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)

    def activate(self, operator: str | None = None) -> None:
        """激活Agent

        将Agent状态切换为ACTIVE。

        Args:
            operator: 操作者标识
        """
        self.status = AgentRegistryStatus.ACTIVE
        self.health_status = HealthStatus.HEALTHY
        self.touch(operator)

    def deactivate(self, operator: str | None = None) -> None:
        """停用Agent

        将Agent状态切换为INACTIVE。

        Args:
            operator: 操作者标识
        """
        self.status = AgentRegistryStatus.INACTIVE
        self.health_status = HealthStatus.UNKNOWN
        self.touch(operator)

    def deprecate(self, operator: str | None = None) -> None:
        """废弃Agent

        将Agent状态切换为DEPRECATED。

        Args:
            operator: 操作者标识
        """
        self.status = AgentRegistryStatus.DEPRECATED
        self.health_status = HealthStatus.UNKNOWN
        self.touch(operator)

    def suspend(self, operator: str | None = None) -> None:
        """暂停Agent

        将Agent状态切换为SUSPENDED。

        Args:
            operator: 操作者标识
        """
        self.status = AgentRegistryStatus.SUSPENDED
        self.health_status = HealthStatus.UNKNOWN
        self.touch(operator)

    def update_health(self, health_status: HealthStatus, operator: str | None = None) -> None:
        """更新健康状态

        Args:
            health_status: 新的健康状态
            operator: 操作者标识
        """
        self.health_status = health_status
        self.touch(operator)
