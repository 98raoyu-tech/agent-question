"""
事件中心业务服务

提供事件发布、订阅管理、事件回放、存储归档和总线配置等核心业务逻辑。
"""

import logging
from datetime import UTC, datetime

from ...common.exceptions import (
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import (
    EventMessageStatus,
    EventPriority,
    EventStoreStatus,
    EventType,
)
from ..domain.event_bus import EventBusConfig
from ..domain.event_message import EventMessage
from ..domain.event_store import EventStoreEntry
from ..domain.event_subscription import EventSubscription
from ..infrastructure.event_center_repository import EventCenterRepository

logger = logging.getLogger(__name__)


class EventCenterService:
    """事件中心业务服务

    提供事件驱动架构的完整业务逻辑，包括事件发布/消费、订阅管理、
    事件回放、存储归档和总线配置。

    Attributes:
        repository: 事件中心仓储实例
    """

    def __init__(self, repository: EventCenterRepository) -> None:
        """初始化事件中心服务

        Args:
            repository: 事件中心仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 事件发布与查询
    # =========================================================================

    async def publish_event(
        self,
        event_type: EventType,
        source: str,
        payload: dict,
        priority: EventPriority = EventPriority.NORMAL,
        operator: str | None = None,
        destination: str = "",
        headers: dict | None = None,
        correlation_id: str | None = None,
    ) -> EventMessage:
        """发布事件

        创建事件消息并将其保存到仓储，同时写入事件存储用于溯源。

        Args:
            event_type: 事件类型
            source: 事件来源标识
            payload: 事件负载数据
            priority: 事件优先级
            operator: 操作者标识
            destination: 事件目标标识
            headers: 事件头部元数据
            correlation_id: 关联ID

        Returns:
            已发布的事件消息实体

        Raises:
            ValidationException: 来源或负载数据为空
        """
        if not source or not source.strip():
            raise ValidationException(message="事件来源不能为空")

        event = EventMessage(
            event_type=event_type,
            priority=priority,
            source=source,
            destination=destination,
            payload=payload,
            headers=headers or {},
            correlation_id=correlation_id,
            created_by=operator,
        )

        event.publish(operator)
        saved_event = await self.repository.save_event(event)

        # 同步写入事件存储
        store_entry = EventStoreEntry(
            event_message_id=saved_event.id,
            event_type=event_type,
            aggregate_id=source,
            aggregate_type=source,
            payload=payload,
            status=EventStoreStatus.ACTIVE,
            stored_at=datetime.now(UTC),
            created_by=operator,
        )
        await self.repository.save_store_entry(store_entry)

        # 更新总线吞吐量
        bus_config = await self.repository.get_bus_config()
        if bus_config is not None and bus_config.is_active:
            bus_config.update_throughput(
                bus_config.current_throughput + 1, operator
            )
            await self.repository.save_bus_config(bus_config)

        logger.info(
            "事件发布成功: id=%s, type=%s, source=%s",
            saved_event.id,
            event_type.value,
            source,
        )

        return saved_event

    async def get_event(self, event_id: str) -> EventMessage:
        """获取事件消息详情

        Args:
            event_id: 事件消息标识

        Returns:
            事件消息实体

        Raises:
            ResourceNotFoundException: 事件消息不存在
        """
        event = await self.repository.find_event_by_id(event_id)
        if event is None:
            raise ResourceNotFoundException(resource_type="事件消息", resource_id=event_id)
        return event

    async def list_events(
        self,
        event_type: EventType | None = None,
        status: EventMessageStatus | None = None,
        pagination: PaginatedRequest | None = None,
    ) -> PaginatedResponse[EventMessage]:
        """分页查询事件消息列表

        Args:
            event_type: 事件类型过滤
            status: 消息状态过滤
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        if pagination is None:
            pagination = PaginatedRequest()

        return await self.repository.find_events(
            event_type=event_type,
            status=status,
            pagination=pagination,
        )

    # =========================================================================
    # 订阅管理
    # =========================================================================

    async def create_subscription(
        self,
        subscription: EventSubscription,
        operator: str | None = None,
    ) -> EventSubscription:
        """创建事件订阅

        Args:
            subscription: 事件订阅实体
            operator: 操作者标识

        Returns:
            创建后的事件订阅实体

        Raises:
            ValidationException: 订阅名称或订阅者ID为空
        """
        if not subscription.name or not subscription.name.strip():
            raise ValidationException(message="订阅名称不能为空")

        if not subscription.subscriber_id or not subscription.subscriber_id.strip():
            raise ValidationException(message="订阅者标识不能为空")

        if not subscription.event_types:
            raise ValidationException(message="订阅事件类型列表不能为空")

        subscription.created_by = operator or subscription.created_by
        saved_subscription = await self.repository.save_subscription(subscription)

        logger.info(
            "事件订阅创建成功: id=%s, name=%s, subscriber=%s",
            saved_subscription.id,
            saved_subscription.name,
            saved_subscription.subscriber_id,
        )

        return saved_subscription

    async def get_subscription(self, subscription_id: str) -> EventSubscription:
        """获取事件订阅详情

        Args:
            subscription_id: 订阅标识

        Returns:
            事件订阅实体

        Raises:
            ResourceNotFoundException: 订阅不存在
        """
        subscription = await self.repository.find_subscription_by_id(subscription_id)
        if subscription is None:
            raise ResourceNotFoundException(
                resource_type="事件订阅", resource_id=subscription_id
            )
        return subscription

    async def list_subscriptions(
        self,
        pagination: PaginatedRequest | None = None,
    ) -> PaginatedResponse[EventSubscription]:
        """分页查询事件订阅列表

        Args:
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        if pagination is None:
            pagination = PaginatedRequest()

        return await self.repository.find_subscriptions(pagination=pagination)

    async def delete_subscription(
        self,
        subscription_id: str,
        operator: str | None = None,
    ) -> bool:
        """删除事件订阅（软删除）

        Args:
            subscription_id: 订阅标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 订阅不存在
        """
        subscription = await self.repository.find_subscription_by_id(subscription_id)
        if subscription is None:
            raise ResourceNotFoundException(
                resource_type="事件订阅", resource_id=subscription_id
            )

        subscription.mark_deleted(operator)
        await self.repository.save_subscription(subscription)

        logger.info("事件订阅删除成功: id=%s", subscription_id)

        return True

    # =========================================================================
    # 事件回放
    # =========================================================================

    async def replay_events(
        self,
        event_type: EventType | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        operator: str | None = None,
    ) -> list[EventMessage]:
        """回放历史事件

        从事件存储中检索指定条件的历史事件，重新发布到事件总线。

        Args:
            event_type: 事件类型过滤
            from_date: 起始日期
            to_date: 截止日期
            operator: 操作者标识

        Returns:
            回放的事件消息列表
        """
        store_entries = []
        entries_response = await self.repository.find_store_entries(
            event_type=event_type,
            status=EventStoreStatus.ACTIVE,
        )
        store_entries = entries_response.items

        if from_date is not None:
            store_entries = [
                e for e in store_entries
                if e.stored_at is not None and e.stored_at >= from_date
            ]

        if to_date is not None:
            store_entries = [
                e for e in store_entries
                if e.stored_at is not None and e.stored_at <= to_date
            ]

        replayed_events: list[EventMessage] = []
        for entry in store_entries:
            replayed_event = EventMessage(
                event_type=entry.event_type,
                source=entry.aggregate_id,
                destination="",
                payload=entry.payload,
                headers={"replayed": True, "original_entry_id": entry.id},
                correlation_id=None,
                created_by=operator,
            )
            replayed_event.publish(operator)
            saved_event = await self.repository.save_event(replayed_event)
            replayed_events.append(saved_event)

        logger.info(
            "事件回放完成: type=%s, from=%s, to=%s, count=%d",
            event_type.value if event_type else "all",
            from_date,
            to_date,
            len(replayed_events),
        )

        return replayed_events

    # =========================================================================
    # 事件存储管理
    # =========================================================================

    async def get_event_store(
        self,
        pagination: PaginatedRequest | None = None,
    ) -> PaginatedResponse[EventStoreEntry]:
        """获取事件存储条目列表

        Args:
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        if pagination is None:
            pagination = PaginatedRequest()

        return await self.repository.find_store_entries(pagination=pagination)

    async def archive_old_events(
        self,
        before_date: datetime,
        operator: str | None = None,
    ) -> int:
        """归档指定日期之前的事件

        Args:
            before_date: 截止日期
            operator: 操作者标识

        Returns:
            归档的事件数量
        """
        entries = await self.repository.find_entries_before_date(before_date)

        archived_count = 0
        for entry in entries:
            entry.archive(operator)
            await self.repository.save_store_entry(entry)
            archived_count += 1

        logger.info(
            "事件归档完成: before=%s, archived_count=%d",
            before_date.isoformat(),
            archived_count,
        )

        return archived_count

    # =========================================================================
    # 事件总线配置
    # =========================================================================

    async def get_bus_config(self) -> EventBusConfig | None:
        """获取事件总线配置

        Returns:
            事件总线配置实体，未初始化返回None
        """
        return await self.repository.get_bus_config()

    async def update_bus_config(
        self,
        config: EventBusConfig,
        operator: str | None = None,
    ) -> EventBusConfig:
        """更新事件总线配置

        Args:
            config: 事件总线配置实体
            operator: 操作者标识

        Returns:
            更新后的事件总线配置实体
        """
        config.touch(operator)
        saved_config = await self.repository.save_bus_config(config)

        logger.info(
            "事件总线配置更新成功: name=%s, broker=%s",
            saved_config.name,
            saved_config.broker_type.value,
        )

        return saved_config

    # =========================================================================
    # 统计信息
    # =========================================================================

    async def get_event_stats(self) -> dict:
        """获取事件统计信息

        Returns:
            包含事件消息、订阅和存储统计的字典
        """
        all_events_response = await self.repository.find_events()
        all_subscriptions_response = await self.repository.find_subscriptions()
        all_store_response = await self.repository.find_store_entries()

        events = all_events_response.items
        subscriptions = all_subscriptions_response.items

        events_by_type: dict[str, int] = {}
        for event in events:
            type_key = event.event_type.value
            events_by_type[type_key] = events_by_type.get(type_key, 0) + 1

        events_by_status: dict[str, int] = {}
        for event in events:
            status_key = event.status.value
            events_by_status[status_key] = events_by_status.get(status_key, 0) + 1

        active_subscriptions = sum(1 for s in subscriptions if s.is_active)
        dead_letter_count = sum(
            1 for e in events if e.status == EventMessageStatus.DEAD_LETTER
        )

        bus_config = await self.repository.get_bus_config()
        bus_info: dict = {}
        if bus_config is not None:
            bus_info = {
                "name": bus_config.name,
                "broker_type": bus_config.broker_type.value,
                "is_active": bus_config.is_active,
                "current_throughput": bus_config.current_throughput,
                "max_throughput": bus_config.max_throughput,
            }

        return {
            "total_events": all_events_response.total,
            "total_subscriptions": all_subscriptions_response.total,
            "active_subscriptions": active_subscriptions,
            "total_store_entries": all_store_response.total,
            "dead_letter_count": dead_letter_count,
            "events_by_type": events_by_type,
            "events_by_status": events_by_status,
            "bus_config": bus_info,
        }
