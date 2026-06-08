"""
知识发布记录实体

定义知识版本的发布和回滚记录实体。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class PublishStatus(str, Enum):
    """发布状态枚举"""

    PUBLISHED = "published"
    """已发布"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


@dataclass
class KnowledgePublishRecord(BaseEntity):
    """知识发布记录实体

    记录知识版本的发布历史和回滚操作。

    Attributes:
        knowledge_source_id: 所属知识源标识
        version_id: 关联版本标识
        published_by: 发布人标识
        published_at: 发布时间
        environment: 发布环境
        status: 发布状态
        rollback_version_id: 回滚目标版本标识
    """

    knowledge_source_id: str = ""
    version_id: str = ""
    published_by: str = ""
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = "production"
    status: PublishStatus = PublishStatus.PUBLISHED
    rollback_version_id: Optional[str] = None

    def rollback(self, target_version_id: str, operator: Optional[str] = None) -> None:
        """执行回滚操作

        仅已发布状态可执行回滚，回滚后记录目标版本。

        Args:
            target_version_id: 回滚目标版本标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 发布状态不允许回滚
        """
        if self.status != PublishStatus.PUBLISHED:
            raise BusinessRuleViolationException(
                rule="PUBLISH_ROLLBACK_TRANSITION",
                message=f"当前发布状态 [{self.status.value}] 不允许回滚，仅 PUBLISHED 状态可操作",
            )
        self.status = PublishStatus.ROLLED_BACK
        self.rollback_version_id = target_version_id
        self.touch(operator)
