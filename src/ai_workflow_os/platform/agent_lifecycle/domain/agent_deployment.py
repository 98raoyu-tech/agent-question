"""
Agent部署实体

管理Agent版本的部署生命周期，支持多种部署策略、流量控制和扩缩容。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import DeploymentEnvironment, DeploymentStatus, DeploymentStrategy


@dataclass
class AgentDeployment(BaseEntity):
    """Agent部署实体

    记录一次部署的完整信息，包括环境、策略、状态和流量控制。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        environment: 部署环境
        deployment_strategy: 部署策略
        status: 部署状态
        deployed_at: 部署完成时间
        rolled_back_at: 回滚时间
        health_check_url: 健康检查地址
        traffic_percentage: 流量百分比（0 ~ 100）
        replicas: 副本数
    """

    agent_id: str = ""
    version_id: str = ""
    environment: DeploymentEnvironment = DeploymentEnvironment.DEV
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.DIRECT
    status: DeploymentStatus = DeploymentStatus.PENDING
    deployed_at: Optional[datetime] = field(default=None)
    rolled_back_at: Optional[datetime] = field(default=None)
    health_check_url: Optional[str] = field(default=None)
    traffic_percentage: int = 0
    replicas: int = 1

    def deploy(self, operator: Optional[str] = None) -> None:
        """执行部署

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 部署状态不允许执行
        """
        if self.status not in (DeploymentStatus.PENDING, DeploymentStatus.ROLLED_BACK):
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_STATUS",
                message=f"部署当前状态为 {self.status.value}，只有待部署或已回滚状态可以执行部署",
            )
        self.status = DeploymentStatus.DEPLOYING
        self.deployed_at = datetime.now(timezone.utc)
        self.traffic_percentage = 100
        self.touch(operator)

    def rollback(self, operator: Optional[str] = None) -> None:
        """执行回滚

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 部署状态不允许回滚
        """
        if self.status not in (DeploymentStatus.ACTIVE, DeploymentStatus.DEPLOYING):
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_ROLLBACK_STATUS",
                message=f"部署当前状态为 {self.status.value}，只有运行中或部署中状态可以回滚",
            )
        self.status = DeploymentStatus.ROLLED_BACK
        self.rolled_back_at = datetime.now(timezone.utc)
        self.traffic_percentage = 0
        self.touch(operator)

    def scale(self, replicas: int, operator: Optional[str] = None) -> None:
        """调整副本数

        Args:
            replicas: 目标副本数
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 副本数不合法或部署状态不允许扩缩容
            ValidationException: 副本数小于1
        """
        if replicas < 1:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_SCALE_REPLICAS",
                message="副本数必须大于等于1",
            )
        if self.status != DeploymentStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_SCALE_STATUS",
                message=f"部署当前状态为 {self.status.value}，只有运行中状态可以扩缩容",
            )
        self.replicas = replicas
        self.touch(operator)

    def set_traffic_percentage(
        self,
        percentage: int,
        operator: Optional[str] = None,
    ) -> None:
        """设置流量百分比

        Args:
            percentage: 流量百分比（0 ~ 100）
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 百分比不合法或部署状态不允许调整流量
        """
        if not 0 <= percentage <= 100:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_TRAFFIC_PERCENTAGE",
                message="流量百分比必须在0到100之间",
            )
        if self.status != DeploymentStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_TRAFFIC_STATUS",
                message=f"部署当前状态为 {self.status.value}，只有运行中状态可以调整流量",
            )
        self.traffic_percentage = percentage
        self.touch(operator)
