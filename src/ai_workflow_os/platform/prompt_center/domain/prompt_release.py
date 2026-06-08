"""
Prompt发布实体

管理Prompt模板版本的发布和部署。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException, ValidationException


class ReleaseStatus(str, Enum):
    """发布状态枚举"""

    PENDING = "pending"
    """待部署"""

    DEPLOYING = "deploying"
    """部署中"""

    ACTIVE = "active"
    """已激活"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


@dataclass
class PromptRelease(BaseEntity):
    """Prompt发布实体

    管理Prompt模板版本的发布、部署和回滚。

    Attributes:
        prompt_id: 关联的Prompt模板标识
        version_id: 关联的版本标识
        release_name: 发布名称
        release_notes: 发布说明
        status: 发布状态
        deployed_at: 部署时间
        rolled_back_at: 回滚时间
        traffic_percentage: 流量百分比
        environment: 部署环境
    """

    prompt_id: str = ""
    version_id: str = ""
    release_name: str = ""
    release_notes: str = ""
    status: ReleaseStatus = ReleaseStatus.PENDING
    deployed_at: datetime | None = field(default=None)
    rolled_back_at: datetime | None = field(default=None)
    traffic_percentage: int = 0
    environment: str = ""

    def deploy(self, operator: str | None = None) -> None:
        """部署发布

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 发布状态不允许部署
        """
        if self.status != ReleaseStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="release_deploy",
                message=f"发布当前状态为{self.status.value}，无法部署",
            )

        self.status = ReleaseStatus.ACTIVE
        self.deployed_at = datetime.now(UTC)
        self.traffic_percentage = 100
        self.touch(operator)

    def rollback(self, operator: str | None = None) -> None:
        """回滚发布

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 发布状态不允许回滚
        """
        if self.status != ReleaseStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="release_rollback",
                message=f"发布当前状态为{self.status.value}，无法回滚",
            )

        self.status = ReleaseStatus.ROLLED_BACK
        self.rolled_back_at = datetime.now(UTC)
        self.traffic_percentage = 0
        self.touch(operator)

    def set_traffic_percentage(
        self,
        percentage: int,
        operator: str | None = None,
    ) -> None:
        """设置流量百分比

        Args:
            percentage: 流量百分比（0-100）
            operator: 操作者标识

        Raises:
            ValidationException: 百分比超出范围
            BusinessRuleViolationException: 发布状态不允许修改流量
        """
        if not 0 <= percentage <= 100:
            raise ValidationException(message="流量百分比必须在0到100之间")

        if self.status != ReleaseStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="release_traffic",
                message=f"发布当前状态为{self.status.value}，无法修改流量",
            )

        self.traffic_percentage = percentage
        self.touch(operator)
