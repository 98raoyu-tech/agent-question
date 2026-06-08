"""
事件中心请求/响应Schema

定义事件发布、订阅管理、事件存储和总线配置相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import (
    BrokerType,
    DeliveryMode,
    EventMessageStatus,
    EventPriority,
    EventStoreStatus,
    EventType,
)

# =============================================================================
# 事件消息Schema
# =============================================================================


class PublishEventRequest(CreateDTO):
    """发布事件请求"""

    event_type: EventType = Field(description="事件类型")
    source: str = Field(min_length=1, max_length=200, description="事件来源标识")
    payload: dict[str, Any] = Field(default_factory=dict, description="事件负载数据")
    priority: EventPriority = Field(default=EventPriority.NORMAL, description="事件优先级")
    destination: str = Field(default="", max_length=200, description="事件目标标识")
    headers: dict[str, Any] = Field(default_factory=dict, description="事件头部元数据")
    correlation_id: str | None = Field(default=None, max_length=64, description="关联ID")


class EventMessageResponse(BaseDTO):
    """事件消息响应"""

    event_type: EventType = Field(description="事件类型")
    priority: EventPriority = Field(description="事件优先级")
    delivery_mode: DeliveryMode = Field(description="投递模式")
    source: str = Field(description="事件来源标识")
    destination: str = Field(description="事件目标标识")
    payload: dict[str, Any] = Field(description="事件负载数据")
    headers: dict[str, Any] = Field(description="事件头部元数据")
    correlation_id: str | None = Field(default=None, description="关联ID")
    status: EventMessageStatus = Field(description="消息状态")
    published_at: datetime | None = Field(default=None, description="发布时间")
    consumed_at: datetime | None = Field(default=None, description="消费时间")
    retry_count: int = Field(description="当前重试次数")
    max_retries: int = Field(description="最大重试次数")
    error_message: str | None = Field(default=None, description="错误信息")


class EventMessageListResponse(BaseModel):
    """事件消息列表响应"""

    items: list[EventMessageResponse] = Field(description="事件消息列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 事件订阅Schema
# =============================================================================


class CreateSubscriptionRequest(CreateDTO):
    """创建事件订阅请求"""

    name: str = Field(min_length=1, max_length=200, description="订阅名称")
    description: str = Field(default="", max_length=2000, description="订阅描述")
    event_types: list[EventType] = Field(min_length=1, description="订阅的事件类型列表")
    subscriber_id: str = Field(min_length=1, max_length=200, description="订阅者标识")
    callback_url: str = Field(default="", max_length=500, description="回调地址")
    is_active: bool = Field(default=True, description="是否激活")
    filter_expression: dict[str, Any] = Field(default_factory=dict, description="过滤表达式")
    delivery_mode: DeliveryMode = Field(
        default=DeliveryMode.AT_LEAST_ONCE, description="投递模式"
    )


class EventSubscriptionResponse(BaseDTO):
    """事件订阅响应"""

    name: str = Field(description="订阅名称")
    description: str = Field(description="订阅描述")
    event_types: list[EventType] = Field(description="订阅的事件类型列表")
    subscriber_id: str = Field(description="订阅者标识")
    callback_url: str = Field(description="回调地址")
    is_active: bool = Field(description="是否激活")
    filter_expression: dict[str, Any] = Field(description="过滤表达式")
    delivery_mode: DeliveryMode = Field(description="投递模式")
    created_by: str | None = Field(default=None, description="创建者标识")
    last_delivered_at: datetime | None = Field(default=None, description="最近投递时间")
    delivery_count: int = Field(description="累计投递次数")
    failure_count: int = Field(description="累计失败次数")


class EventSubscriptionListResponse(BaseModel):
    """事件订阅列表响应"""

    items: list[EventSubscriptionResponse] = Field(description="事件订阅列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 事件回放Schema
# =============================================================================


class ReplayEventsRequest(BaseModel):
    """回放事件请求"""

    event_type: EventType | None = Field(default=None, description="事件类型过滤")
    from_date: datetime | None = Field(default=None, description="起始日期")
    to_date: datetime | None = Field(default=None, description="截止日期")
    operator: str | None = Field(default=None, max_length=200, description="操作者标识")


class ReplayEventsResponse(BaseModel):
    """回放事件响应"""

    replayed_count: int = Field(description="回放事件数量")
    events: list[EventMessageResponse] = Field(description="回放的事件列表")


# =============================================================================
# 事件存储Schema
# =============================================================================


class EventStoreEntryResponse(BaseDTO):
    """事件存储条目响应"""

    event_message_id: str = Field(description="关联的事件消息标识")
    event_type: EventType = Field(description="事件类型")
    aggregate_id: str = Field(description="聚合根标识")
    aggregate_type: str = Field(description="聚合根类型")
    payload: dict[str, Any] = Field(description="事件负载快照")
    status: EventStoreStatus = Field(description="存储状态")
    stored_at: datetime | None = Field(default=None, description="入库时间")
    archived_at: datetime | None = Field(default=None, description="归档时间")
    ttl_days: int = Field(description="存活天数")


class EventStoreListResponse(BaseModel):
    """事件存储列表响应"""

    items: list[EventStoreEntryResponse] = Field(description="事件存储条目列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class ArchiveEventsRequest(BaseModel):
    """归档事件请求"""

    before_date: datetime = Field(description="截止日期（此日期之前的事件将被归档）")


class ArchiveEventsResponse(BaseModel):
    """归档事件响应"""

    archived_count: int = Field(description="归档的事件数量")


# =============================================================================
# 事件总线配置Schema
# =============================================================================


class EventBusConfigResponse(BaseDTO):
    """事件总线配置响应"""

    name: str = Field(description="总线名称")
    broker_type: BrokerType = Field(description="消息代理类型")
    connection_config: dict[str, Any] = Field(description="连接配置")
    is_active: bool = Field(description="是否活跃")
    topic_prefix: str = Field(description="主题前缀")
    consumer_group: str = Field(description="消费者组标识")
    max_throughput: int = Field(description="最大吞吐量")
    current_throughput: int = Field(description="当前吞吐量")


class UpdateBusConfigRequest(BaseModel):
    """更新事件总线配置请求"""

    name: str = Field(min_length=1, max_length=200, description="总线名称")
    broker_type: BrokerType = Field(description="消息代理类型")
    connection_config: dict[str, Any] = Field(default_factory=dict, description="连接配置")
    is_active: bool = Field(default=True, description="是否活跃")
    topic_prefix: str = Field(default="", max_length=100, description="主题前缀")
    consumer_group: str = Field(default="", max_length=200, description="消费者组标识")
    max_throughput: int = Field(default=1000, ge=1, description="最大吞吐量")


# =============================================================================
# 统计Schema
# =============================================================================


class EventStatsResponse(BaseModel):
    """事件统计响应"""

    total_events: int = Field(description="事件消息总数")
    total_subscriptions: int = Field(description="订阅总数")
    active_subscriptions: int = Field(description="活跃订阅数")
    total_store_entries: int = Field(description="存储条目总数")
    dead_letter_count: int = Field(description="死信队列消息数")
    events_by_type: dict[str, int] = Field(description="按事件类型统计")
    events_by_status: dict[str, int] = Field(description="按消息状态统计")
    bus_config: dict[str, Any] = Field(description="总线配置概要")
