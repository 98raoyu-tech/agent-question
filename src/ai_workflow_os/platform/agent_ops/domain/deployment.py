"""
部署实体

定义Agent部署的核心业务实体，包含部署配置、状态管理和部署操作。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import (
    DeploymentStatus,
    DeploymentStrategy,
    Environment,
    HealthStatus,
)


@dataclass
class Deployment(BaseEntity):
    """部署实体

    管理Agent的部署生命周期，支持灰度发布、蓝绿部署等多种策略。

    Attributes:
        agent_id: Agent标识
        version_id: 版本标识
        environment: 部署环境
        strategy: 部署策略
        status: 部署状态
        canary_percentage: 灰度发布百分比
        blue_green_active_slot: 蓝绿部署活跃槽位（blue/green）
        deployed_at: 部署完成时间
        config: 部署配置
        health_status: 健康状态
    """

    agent_id: str = ""
    version_id: str = ""
    environment: Environment = Environment.DEV
    strategy: DeploymentStrategy = DeploymentStrategy.DIRECT
    status: DeploymentStatus = DeploymentStatus.PENDING
    canary_percentage: int = 0
    blue_green_active_slot: str = "blue"
    deployed_at: Optional[datetime] = None
    config: dict[str, Any] = field(default_factory=dict)
    health_status: HealthStatus = HealthStatus.UNKNOWN

    def deploy(self, operator: Optional[str] = None) -> None:
        """执行部署

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 部署状态不允许部署
        """
        # 只有待部署或失败状态才能重新部署
        if self.status not in (DeploymentStatus.PENDING, DeploymentStatus.FAILED):
            raise ValueError(f"当前状态 {self.status.value} 不允许部署")

        self.status = DeploymentStatus.DEPLOYING
        self.health_status = HealthStatus.UNKNOWN
        self.touch(operator)

        # 根据策略设置初始状态
        if self.strategy == DeploymentStrategy.CANARY:
            self.canary_percentage = 10
        elif self.strategy == DeploymentStrategy.BLUE_GREEN:
            self.blue_green_active_slot = "blue"

        # 模拟部署完成
        self.status = DeploymentStatus.ACTIVE
        self.deployed_at = datetime.now(timezone.utc)
        self.health_status = HealthStatus.HEALTHY
        self.touch(operator)

    def rollback(self, operator: Optional[str] = None) -> None:
        """回滚部署

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 部署状态不允许回滚
        """
        # 只有激活状态才能回滚
        if self.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"当前状态 {self.status.value} 不允许回滚")

        self.status = DeploymentStatus.ROLLED_BACK
        self.health_status = HealthStatus.UNKNOWN
        self.canary_percentage = 0
        self.touch(operator)

    def promote_canary(self, percentage: int, operator: Optional[str] = None) -> None:
        """提升灰度发布比例

        Args:
            percentage: 目标百分比（0-100）
            operator: 操作者标识

        Raises:
            ValueError: 非灰度策略或百分比无效
        """
        if self.strategy != DeploymentStrategy.CANARY:
            raise ValueError("只有灰度发布策略才能提升灰度比例")

        if percentage < 0 or percentage > 100:
            raise ValueError("灰度百分比必须在0-100之间")

        if self.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"当前状态 {self.status.value} 不允许提升灰度比例")

        self.canary_percentage = percentage
        self.touch(operator)

        # 灰度比例达到100%时，更新状态为完全激活
        if percentage == 100:
            self.health_status = HealthStatus.HEALTHY

    def switch_blue_green(self, operator: Optional[str] = None) -> None:
        """切换蓝绿部署槽位

        Args:
            operator: 操作者标识

        Raises:
            ValueError: 非蓝绿策略或状态不允许
        """
        if self.strategy != DeploymentStrategy.BLUE_GREEN:
            raise ValueError("只有蓝绿部署策略才能切换槽位")

        if self.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"当前状态 {self.status.value} 不允许切换槽位")

        # 切换槽位
        self.blue_green_active_slot = (
            "green" if self.blue_green_active_slot == "blue" else "blue"
        )
        self.touch(operator)

    def update_health(self, health_status: HealthStatus, operator: Optional[str] = None) -> None:
        """更新健康状态

        Args:
            health_status: 新的健康状态
            operator: 操作者标识
        """
        self.health_status = health_status
        self.touch(operator)

    def to_canary_full(self, operator: Optional[str] = None) -> None:
        """将灰度发布提升为全量发布

        Args:
            operator: 操作者标识
        """
        self.promote_canary(100, operator)
