"""
知识版本实体

定义知识源的版本管理实体，支持版本的创建、发布和切换。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class VersionStatus(str, Enum):
    """版本状态枚举"""

    DRAFT = "draft"
    """草稿"""

    REVIEW = "review"
    """审核中"""

    APPROVED = "approved"
    """已批准"""

    PUBLISHED = "published"
    """已发布"""


@dataclass
class KnowledgeVersion(BaseEntity):
    """知识版本实体

    记录知识源的版本快照，支持版本的流转和发布。

    Attributes:
        knowledge_source_id: 所属知识源标识
        version_number: 版本号
        change_log: 变更日志
        snapshot: 版本快照数据
        is_current: 是否为当前版本
        status: 版本状态
    """

    knowledge_source_id: str = ""
    version_number: int = 1
    change_log: str = ""
    snapshot: dict[str, Any] = field(default_factory=dict)
    is_current: bool = False
    status: VersionStatus = VersionStatus.DRAFT

    def publish(self, operator: Optional[str] = None) -> None:
        """发布版本

        仅已批准的版本可以发布，发布后状态变为已发布并设为当前版本。

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 版本状态不允许发布
        """
        if self.status != VersionStatus.APPROVED:
            raise BusinessRuleViolationException(
                rule="VERSION_PUBLISH_TRANSITION",
                message=f"当前版本状态 [{self.status.value}] 不允许发布，仅 APPROVED 状态可发布",
            )
        self.status = VersionStatus.PUBLISHED
        self.is_current = True
        self.touch(operator)

    def set_as_current(self, operator: Optional[str] = None) -> None:
        """将版本设为当前版本

        仅已发布状态的版本可设为当前版本。

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 版本状态不允许设为当前版本
        """
        if self.status != VersionStatus.PUBLISHED:
            raise BusinessRuleViolationException(
                rule="VERSION_CURRENT_TRANSITION",
                message=f"当前版本状态 [{self.status.value}] 不允许设为当前版本，仅 PUBLISHED 状态可以",
            )
        self.is_current = True
        self.touch(operator)
