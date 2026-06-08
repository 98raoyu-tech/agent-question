"""
事件中心 FastAPI路由

提供事件发布、订阅管理、事件回放、存储归档和总线配置的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.event_center_service import EventCenterService
from ..domain.enums import EventMessageStatus, EventType
from ..domain.event_bus import EventBusConfig
from ..domain.event_subscription import EventSubscription
from ..infrastructure.event_center_repository import EventCenterRepository
from .schemas import (
    ArchiveEventsRequest,
    ArchiveEventsResponse,
    CreateSubscriptionRequest,
    EventBusConfigResponse,
    EventMessageListResponse,
    EventMessageResponse,
    EventStatsResponse,
    EventStoreEntryResponse,
    EventStoreListResponse,
    EventSubscriptionListResponse,
    EventSubscriptionResponse,
    PublishEventRequest,
    ReplayEventsRequest,
    ReplayEventsResponse,
    UpdateBusConfigRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/event-center", tags=["事件中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_event_center_repository = EventCenterRepository()
_event_center_service = EventCenterService(_event_center_repository)


# =============================================================================
# 事件消息端点
# =============================================================================


@router.post(
    "/events",
    response_model=EventMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发布事件",
    description="发布一个新的事件消息到事件总线",
)
async def publish_event(request: PublishEventRequest) -> EventMessageResponse:
    """发布事件

    Args:
        request: 发布事件请求

    Returns:
        事件消息响应

    Raises:
        HTTPException: 发布失败
    """
    try:
        event = await _event_center_service.publish_event(
            event_type=request.event_type,
            source=request.source,
            payload=request.payload,
            priority=request.priority,
            operator=request.created_by,
            destination=request.destination,
            headers=request.headers,
            correlation_id=request.correlation_id,
        )

        return _to_event_message_response(event)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/events",
    response_model=EventMessageListResponse,
    summary="查询事件列表",
    description="分页查询事件消息列表",
)
async def list_events(
    event_type: EventType | None = Query(default=None, description="事件类型过滤"),
    status_filter: EventMessageStatus | None = Query(
        default=None, alias="status", description="消息状态过滤"
    ),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> EventMessageListResponse:
    """查询事件列表

    Args:
        event_type: 事件类型过滤
        status_filter: 消息状态过滤
        page: 页码
        page_size: 每页大小

    Returns:
        事件消息列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _event_center_service.list_events(
        event_type=event_type,
        status=status_filter,
        pagination=pagination,
    )

    return EventMessageListResponse(
        items=[_to_event_message_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/events/{event_id}",
    response_model=EventMessageResponse,
    summary="获取事件详情",
    description="根据ID获取事件消息的详细信息",
)
async def get_event(event_id: str) -> EventMessageResponse:
    """获取事件详情

    Args:
        event_id: 事件消息标识

    Returns:
        事件消息响应

    Raises:
        HTTPException: 事件不存在
    """
    try:
        event = await _event_center_service.get_event(event_id)
        return _to_event_message_response(event)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 事件回放端点
# =============================================================================


@router.post(
    "/events/replay",
    response_model=ReplayEventsResponse,
    summary="回放事件",
    description="根据条件回放历史事件，重新发布到事件总线",
)
async def replay_events(request: ReplayEventsRequest) -> ReplayEventsResponse:
    """回放事件

    Args:
        request: 回放事件请求

    Returns:
        回放事件响应

    Raises:
        HTTPException: 回放失败
    """
    try:
        events = await _event_center_service.replay_events(
            event_type=request.event_type,
            from_date=request.from_date,
            to_date=request.to_date,
            operator=request.operator,
        )

        return ReplayEventsResponse(
            replayed_count=len(events),
            events=[_to_event_message_response(e) for e in events],
        )

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 事件订阅端点
# =============================================================================


@router.post(
    "/subscriptions",
    response_model=EventSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建事件订阅",
    description="创建一个新的事件订阅",
)
async def create_subscription(
    request: CreateSubscriptionRequest,
) -> EventSubscriptionResponse:
    """创建事件订阅

    Args:
        request: 创建订阅请求

    Returns:
        事件订阅响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        subscription = EventSubscription(
            name=request.name,
            description=request.description,
            event_types=request.event_types,
            subscriber_id=request.subscriber_id,
            callback_url=request.callback_url,
            is_active=request.is_active,
            filter_expression=request.filter_expression,
            delivery_mode=request.delivery_mode,
            tenant_id=request.tenant_id,
        )

        created_subscription = await _event_center_service.create_subscription(
            subscription=subscription,
            operator=request.created_by,
        )

        return _to_subscription_response(created_subscription)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/subscriptions",
    response_model=EventSubscriptionListResponse,
    summary="查询订阅列表",
    description="分页查询事件订阅列表",
)
async def list_subscriptions(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> EventSubscriptionListResponse:
    """查询订阅列表

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        事件订阅列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _event_center_service.list_subscriptions(pagination=pagination)

    return EventSubscriptionListResponse(
        items=[_to_subscription_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=EventSubscriptionResponse,
    summary="获取订阅详情",
    description="根据ID获取事件订阅的详细信息",
)
async def get_subscription(subscription_id: str) -> EventSubscriptionResponse:
    """获取订阅详情

    Args:
        subscription_id: 订阅标识

    Returns:
        事件订阅响应

    Raises:
        HTTPException: 订阅不存在
    """
    try:
        subscription = await _event_center_service.get_subscription(subscription_id)
        return _to_subscription_response(subscription)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除订阅",
    description="软删除事件订阅",
)
async def delete_subscription(subscription_id: str) -> None:
    """删除订阅

    Args:
        subscription_id: 订阅标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _event_center_service.delete_subscription(subscription_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 事件存储端点
# =============================================================================


@router.get(
    "/store",
    response_model=EventStoreListResponse,
    summary="查询事件存储",
    description="分页查询事件存储条目列表",
)
async def get_event_store(
    event_type: EventType | None = Query(default=None, description="事件类型过滤"),
    status_filter: str | None = Query(default=None, alias="status", description="存储状态过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> EventStoreListResponse:
    """查询事件存储

    Args:
        event_type: 事件类型过滤
        status_filter: 存储状态过滤
        page: 页码
        page_size: 每页大小

    Returns:
        事件存储列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _event_center_service.get_event_store(pagination=pagination)

    return EventStoreListResponse(
        items=[_to_store_entry_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post(
    "/store/archive",
    response_model=ArchiveEventsResponse,
    summary="归档事件",
    description="归档指定日期之前的事件存储条目",
)
async def archive_old_events(request: ArchiveEventsRequest) -> ArchiveEventsResponse:
    """归档事件

    Args:
        request: 归档事件请求

    Returns:
        归档事件响应

    Raises:
        HTTPException: 归档失败
    """
    try:
        archived_count = await _event_center_service.archive_old_events(
            before_date=request.before_date,
        )

        return ArchiveEventsResponse(archived_count=archived_count)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 事件总线配置端点
# =============================================================================


@router.get(
    "/bus-config",
    response_model=EventBusConfigResponse | None,
    summary="获取总线配置",
    description="获取事件总线的当前配置",
)
async def get_bus_config() -> EventBusConfigResponse | None:
    """获取总线配置

    Returns:
        事件总线配置响应，未初始化返回null
    """
    config = await _event_center_service.get_bus_config()

    if config is None:
        return None

    return _to_bus_config_response(config)


@router.put(
    "/bus-config",
    response_model=EventBusConfigResponse,
    summary="更新总线配置",
    description="更新事件总线配置",
)
async def update_bus_config(request: UpdateBusConfigRequest) -> EventBusConfigResponse:
    """更新总线配置

    Args:
        request: 更新总线配置请求

    Returns:
        更新后的事件总线配置响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        config = EventBusConfig(
            name=request.name,
            broker_type=request.broker_type,
            connection_config=request.connection_config,
            is_active=request.is_active,
            topic_prefix=request.topic_prefix,
            consumer_group=request.consumer_group,
            max_throughput=request.max_throughput,
        )

        updated_config = await _event_center_service.update_bus_config(config=config)

        return _to_bus_config_response(updated_config)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 统计端点
# =============================================================================


@router.get(
    "/stats",
    response_model=EventStatsResponse,
    summary="获取事件统计",
    description="获取事件中心的综合统计信息",
)
async def get_event_stats() -> EventStatsResponse:
    """获取事件统计

    Returns:
        事件统计响应
    """
    stats = await _event_center_service.get_event_stats()

    return EventStatsResponse(
        total_events=stats["total_events"],
        total_subscriptions=stats["total_subscriptions"],
        active_subscriptions=stats["active_subscriptions"],
        total_store_entries=stats["total_store_entries"],
        dead_letter_count=stats["dead_letter_count"],
        events_by_type=stats["events_by_type"],
        events_by_status=stats["events_by_status"],
        bus_config=stats["bus_config"],
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_event_message_response(event) -> EventMessageResponse:
    """将事件消息实体转换为响应Schema

    Args:
        event: 事件消息实体

    Returns:
        事件消息响应
    """
    return EventMessageResponse(
        id=event.id,
        event_type=event.event_type,
        priority=event.priority,
        delivery_mode=event.delivery_mode,
        source=event.source,
        destination=event.destination,
        payload=event.payload,
        headers=event.headers,
        correlation_id=event.correlation_id,
        status=event.status,
        published_at=event.published_at,
        consumed_at=event.consumed_at,
        retry_count=event.retry_count,
        max_retries=event.max_retries,
        error_message=event.error_message,
        created_at=event.created_at,
        updated_at=event.updated_at,
        tenant_id=event.tenant_id,
    )


def _to_subscription_response(subscription: EventSubscription) -> EventSubscriptionResponse:
    """将事件订阅实体转换为响应Schema

    Args:
        subscription: 事件订阅实体

    Returns:
        事件订阅响应
    """
    return EventSubscriptionResponse(
        id=subscription.id,
        name=subscription.name,
        description=subscription.description,
        event_types=subscription.event_types,
        subscriber_id=subscription.subscriber_id,
        callback_url=subscription.callback_url,
        is_active=subscription.is_active,
        filter_expression=subscription.filter_expression,
        delivery_mode=subscription.delivery_mode,
        created_by=subscription.created_by,
        last_delivered_at=subscription.last_delivered_at,
        delivery_count=subscription.delivery_count,
        failure_count=subscription.failure_count,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
        tenant_id=subscription.tenant_id,
    )


def _to_store_entry_response(entry) -> EventStoreEntryResponse:
    """将事件存储条目实体转换为响应Schema

    Args:
        entry: 事件存储条目实体

    Returns:
        事件存储条目响应
    """
    return EventStoreEntryResponse(
        id=entry.id,
        event_message_id=entry.event_message_id,
        event_type=entry.event_type,
        aggregate_id=entry.aggregate_id,
        aggregate_type=entry.aggregate_type,
        payload=entry.payload,
        status=entry.status,
        stored_at=entry.stored_at,
        archived_at=entry.archived_at,
        ttl_days=entry.ttl_days,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        tenant_id=entry.tenant_id,
    )


def _to_bus_config_response(config: EventBusConfig) -> EventBusConfigResponse:
    """将事件总线配置实体转换为响应Schema

    Args:
        config: 事件总线配置实体

    Returns:
        事件总线配置响应
    """
    return EventBusConfigResponse(
        id=config.id,
        name=config.name,
        broker_type=config.broker_type,
        connection_config=config.connection_config,
        is_active=config.is_active,
        topic_prefix=config.topic_prefix,
        consumer_group=config.consumer_group,
        max_throughput=config.max_throughput,
        current_throughput=config.current_throughput,
        created_at=config.created_at,
        updated_at=config.updated_at,
        tenant_id=config.tenant_id,
    )
