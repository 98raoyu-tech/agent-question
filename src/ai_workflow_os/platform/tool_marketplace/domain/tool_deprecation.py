"""
工具废弃实体

管理工具从废弃公告到完全下线的生命周期。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class DeprecationStatus(str, Enum):
    """废弃状态枚举"""

    ANNOUNCED = "announced"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class ToolDeprecation(BaseEntity):
    """工具废弃实体

    记录工具的废弃计划和迁移指引。

    Attributes:
        tool_id: 关联的工具标识
        reason: 废弃原因
        deprecated_by: 发起人标识
        deprecated_at: 发起时间
        sunset_date: 计划下线日期
        replacement_tool_id: 替代工具标识
        migration_guide: 迁移指引文档
        status: 废弃状态
    """

    tool_id: str = ""
    reason: str = ""
    deprecated_by: str = ""
    deprecated_at: Optional[datetime] = field(default=None)
    sunset_date: Optional[datetime] = field(default=None)
    replacement_tool_id: Optional[str] = field(default=None)
    migration_guide: str = ""
    status: DeprecationStatus = DeprecationStatus.ANNOUNCED

    def announce(self, operator: Optional[str] = None) -> None:
        """发布公告

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 当前状态不允许该操作
        """
        if self.status != DeprecationStatus.ANNOUNCED:
            raise BusinessRuleViolationException(
                rule="DEPRECATION_STATUS_TRANSITION",
                message=f"废弃计划 [{self.id}] 当前状态为 {self.status.value}，不允许重新发布公告",
            )
        self.deprecated_at = datetime.now(timezone.utc)
        self.touch(operator)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活废弃（开始限制新用户使用）

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 当前状态不允许该操作
        """
        if self.status != DeprecationStatus.ANNOUNCED:
            raise BusinessRuleViolationException(
                rule="DEPRECATION_STATUS_TRANSITION",
                message=f"废弃计划 [{self.id}] 当前状态为 {self.status.value}，不允许激活",
            )
        self.status = DeprecationStatus.ACTIVE
        self.touch(operator)

    def complete(self, operator: Optional[str] = None) -> None:
        """完成废弃（工具完全下线）

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 当前状态不允许该操作
        """
        if self.status != DeprecationStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="DEPRECATION_STATUS_TRANSITION",
                message=f"废弃计划 [{self.id}] 当前状态为 {self.status.value}，不允许完成",
            )
        self.status = DeprecationStatus.COMPLETED
        self.touch(operator)
