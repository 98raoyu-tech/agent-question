"""
事件中心仓储实现

提供事件消息、事件订阅、事件存储条目和事件总线配置的内存存储实现。
"""

import logging
from datetime import datetime

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import EventMessageStatus, EventStoreStatus, EventType
from ..domain.event_bus import EventBusConfig
from ..domain.event_message import EventMessage
from ..domain.event_store import EventStoreEntry
from ..domain.event_subscription import EventSubscription

logger = logging.getLogger(__name__)


class EventCenterRepository:
    """事件中心仓储实现

    基于内存字典的仓储实现，管理事件消息、订阅、存储和总线配置的持久化。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._events: dict[str, EventMessage] = {}
        self._subscriptions: dict[str, EventSubscription] = {}
        self._store_entries: dict[str, EventStoreEntry] = {}
        self._bus_config: EventBusConfig | None = None

    # =========================================================================
    # 事件消息操作
    # =========================================================================

    async def save_event(self, event: EventMessage) -> EventMessage:
        """保存事件消息

        Args:
            event: 事件消息实体

        Returns:
            保存后的事件消息实体
        """
        self._events[event.id] = event
        return event

    async def find_event_by_id(self, event_id: str) -> EventMessage | None:
        """根据ID查找事件消息

        Args:
            event_id: 事件消息标识

        Returns:
            事件消息实体，未找到返回None
        """
        event = self._events.get(event_id)
        if event is not None and event.is_deleted:
            return None
        return event

    async def find_events(
        self,
        event_type: EventType | None = None,
        status: EventMessageStatus | None = None,
        pagination: PaginatedRequest | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[EventMessage]:
        """查询事件消息列表

        Args:
            event_type: 事件类型过滤
            status: 消息状态过滤
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        events = [e for e in self._events.values() if not e.is_deleted]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if status is not None:
            events = [e for e in events if e.status == status]

        if tenant_id is not None:
            events = [e for e in events if e.tenant_id == tenant_id]

        events.sort(key=lambda e: e.created_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(events)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = events[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # =========================================================================
    # 订阅操作
    # =========================================================================

    async def save_subscription(self, subscription: EventSubscription) -> EventSubscription:
        """保存事件订阅

        Args:
            subscription: 事件订阅实体

        Returns:
            保存后的事件订阅实体
        """
        self._subscriptions[subscription.id] = subscription
        return subscription

    async def find_subscription_by_id(self, subscription_id: str) -> EventSubscription | None:
        """根据ID查找事件订阅

        Args:
            subscription_id: 订阅标识

        Returns:
            事件订阅实体，未找到返回None
        """
        subscription = self._subscriptions.get(subscription_id)
        if subscription is not None and subscription.is_deleted:
            return None
        return subscription

    async def find_subscriptions(
        self,
        pagination: PaginatedRequest | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[EventSubscription]:
        """查询事件订阅列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        subscriptions = [s for s in self._subscriptions.values() if not s.is_deleted]

        if tenant_id is not None:
            subscriptions = [s for s in subscriptions if s.tenant_id == tenant_id]

        subscriptions.sort(key=lambda s: s.created_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(subscriptions)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = subscriptions[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def find_active_subscriptions_by_event_type(
        self,
        event_type: EventType,
    ) -> list[EventSubscription]:
        """查找订阅了指定事件类型的所有活跃订阅

        Args:
            event_type: 事件类型

        Returns:
            匹配的活跃订阅列表
        """
        return [
            s for s in self._subscriptions.values()
            if not s.is_deleted
            and s.is_active
            and event_type in s.event_types
        ]

    async def delete_subscription(self, subscription_id: str) -> bool:
        """从存储中移除事件订阅

        Args:
            subscription_id: 订阅标识

        Returns:
            是否删除成功
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False

    # =========================================================================
    # 事件存储操作
    # =========================================================================

    async def save_store_entry(self, entry: EventStoreEntry) -> EventStoreEntry:
        """保存事件存储条目

        Args:
            entry: 事件存储条目实体

        Returns:
            保存后的事件存储条目实体
        """
        self._store_entries[entry.id] = entry
        return entry

    async def find_store_entries(
        self,
        event_type: EventType | None = None,
        status: EventStoreStatus | None = None,
        pagination: PaginatedRequest | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[EventStoreEntry]:
        """查询事件存储条目列表

        Args:
            event_type: 事件类型过滤
            status: 存储状态过滤
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        entries = [e for e in self._store_entries.values() if not e.is_deleted]

        if event_type is not None:
            entries = [e for e in entries if e.event_type == event_type]

        if status is not None:
            entries = [e for e in entries if e.status == status]

        if tenant_id is not None:
            entries = [e for e in entries if e.tenant_id == tenant_id]

        entries.sort(key=lambda e: e.stored_at or e.created_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(entries)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = entries[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def find_expired_entries(self) -> list[EventStoreEntry]:
        """查找所有已过期的事件存储条目

        Returns:
            已过期且状态为ACTIVE的条目列表
        """
        return [
            entry for entry in self._store_entries.values()
            if not entry.is_deleted
            and entry.status == EventStoreStatus.ACTIVE
            and entry.is_expired()
        ]

    async def find_entries_before_date(
        self,
        before_date: datetime,
    ) -> list[EventStoreEntry]:
        """查找指定日期之前存储的事件条目

        Args:
            before_date: 截止日期

        Returns:
            指定日期之前存储的活跃条目列表
        """
        return [
            entry for entry in self._store_entries.values()
            if not entry.is_deleted
            and entry.status == EventStoreStatus.ACTIVE
            and entry.stored_at is not None
            and entry.stored_at < before_date
        ]

    # =========================================================================
    # 事件总线配置操作
    # =========================================================================

    async def save_bus_config(self, config: EventBusConfig) -> EventBusConfig:
        """保存事件总线配置

        Args:
            config: 事件总线配置实体

        Returns:
            保存后的事件总线配置实体
        """
        self._bus_config = config
        return config

    async def get_bus_config(self) -> EventBusConfig | None:
        """获取事件总线配置

        Returns:
            事件总线配置实体，未初始化返回None
        """
        return self._bus_config
