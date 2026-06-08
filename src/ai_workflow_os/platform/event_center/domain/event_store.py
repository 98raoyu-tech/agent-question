"""
事件存储条目实体

定义事件存储（Event Store）的核心领域实体，用于事件溯源和审计追踪。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from ...common.base_entity import BaseEntity
from .enums import EventStoreStatus, EventType


@dataclass
class EventStoreEntry(BaseEntity):
    """事件存储条目实体

    记录已发生的领域事件，支持事件溯源、回放和历史审计。
    每条记录关联一个事件消息，包含聚合根信息和生命周期管理。

    Attributes:
        event_message_id: 关联的事件消息标识
        event_type: 事件类型
        aggregate_id: 聚合根标识
        aggregate_type: 聚合根类型
        payload: 事件负载快照
        status: 存储状态
        stored_at: 入库时间
        archived_at: 归档时间
        ttl_days: 存活天数（过期后可归档或清除）
    """

    event_message_id: str = ""
    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    aggregate_id: str = ""
    aggregate_type: str = ""
    payload: dict = field(default_factory=dict)
    status: EventStoreStatus = EventStoreStatus.ACTIVE
    stored_at: datetime | None = field(default=None)
    archived_at: datetime | None = field(default=None)
    ttl_days: int = field(default=90)

    def archive(self, operator: str | None = None) -> None:
        """归档事件存储条目

        Args:
            operator: 操作者标识
        """
        self.status = EventStoreStatus.ARCHIVED
        self.archived_at = datetime.now(UTC)
        self.touch(operator)

    def purge(self, operator: str | None = None) -> None:
        """清除事件存储条目

        将状态标记为PURGED，表示条目已被清除（软删除）。

        Args:
            operator: 操作者标识
        """
        self.status = EventStoreStatus.PURGED
        self.touch(operator)

    def is_expired(self) -> bool:
        """判断事件存储条目是否已过期

        基于stored_at和ttl_days计算是否超过存活期限。

        Returns:
            已过期返回True
        """
        if self.stored_at is None:
            return False

        expiration_time = self.stored_at + timedelta(days=self.ttl_days)
        return datetime.now(UTC) > expiration_time
