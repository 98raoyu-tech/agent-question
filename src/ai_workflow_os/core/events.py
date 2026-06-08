"""
事件总线模块

实现基于 asyncio.Queue 的发布/订阅模式事件总线，
支持异步事件的发布、订阅与消费。
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class EventMessage:
    """
    事件消息数据结构

    Attributes:
        event_type: 事件类型标识符
        source: 事件来源
        payload: 事件负载数据
        timestamp: 事件发生时间戳（UTC）
        correlation_id: 关联 ID，用于链路追踪
    """

    event_type: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex)


# 事件处理器类型：接受 EventMessage 的异步协程函数
EventHandler = Callable[[EventMessage], Coroutine[Any, Any, None]]


class EventBus:
    """
    事件总线

    提供发布/订阅模式的事件处理机制，支持：
    - 按事件类型订阅与取消订阅
    - 异步发布事件到内部队列
    - 启动/停止事件消费循环

    使用示例：
        event_bus = EventBus()

        async def on_agent_started(event: EventMessage):
            print(f"Agent 启动: {event.payload}")

        event_bus.subscribe("agent.started", on_agent_started)
        await event_bus.start()

        await event_bus.publish("agent.started", {"agent_id": "chat-001"})

        await event_bus.stop()
    """

    def __init__(self, max_queue_size: int = 10000) -> None:
        """
        初始化事件总线

        Args:
            max_queue_size: 事件队列最大容量，防止内存溢出
        """
        self._max_queue_size = max_queue_size
        self._queue: asyncio.Queue[Optional[EventMessage]] = asyncio.Queue(maxsize=max_queue_size)
        self._subscribers: Dict[str, Set[EventHandler]] = {}
        self._running: bool = False
        self._consumer_task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        订阅指定类型的事件

        Args:
            event_type: 事件类型标识符
            handler: 异步事件处理器
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(handler)
        logger.debug("已订阅事件类型 '%s'，当前订阅者数量: %d", event_type, len(self._subscribers[event_type]))

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        取消订阅指定类型的事件

        Args:
            event_type: 事件类型标识符
            handler: 异步事件处理器
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(handler)
            logger.debug("已取消订阅事件类型 '%s'，剩余订阅者数量: %d", event_type, len(self._subscribers[event_type]))
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    async def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None, source: str = "system") -> EventMessage:
        """
        发布事件到事件总线

        Args:
            event_type: 事件类型标识符
            payload: 事件负载数据
            source: 事件来源标识

        Returns:
            创建的 EventMessage 实例
        """
        event = EventMessage(
            event_type=event_type,
            source=source,
            payload=payload or {},
        )

        try:
            self._queue.put_nowait(event)
            logger.debug("事件已发布: type=%s, source=%s, correlation_id=%s", event_type, source, event.correlation_id)
        except asyncio.QueueFull:
            logger.error("事件队列已满 (max=%d)，丢弃事件: type=%s", self._max_queue_size, event_type)

        return event

    async def start(self) -> None:
        """
        启动事件消费循环

        创建后台任务持续从队列中消费事件并分发给订阅者。
        """
        if self._running:
            logger.warning("事件总线已在运行中")
            return

        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_events())
        logger.info("事件总线已启动，最大队列容量: %d", self._max_queue_size)

    async def stop(self) -> None:
        """
        停止事件消费循环

        发送终止信号并等待消费者任务完成。
        """
        if not self._running:
            logger.warning("事件总线未在运行")
            return

        self._running = False
        # 发送 None 作为终止信号
        await self._queue.put(None)

        if self._consumer_task is not None:
            try:
                await asyncio.wait_for(self._consumer_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("事件消费任务停止超时，强制取消")
                self._consumer_task.cancel()
            finally:
                self._consumer_task = None

        logger.info("事件总线已停止")

    async def _consume_events(self) -> None:
        """
        事件消费循环（内部方法）

        持续从队列中取出事件并分发给所有订阅者。
        收到 None 时终止循环。
        """
        logger.info("事件消费循环已启动")

        while self._running:
            try:
                event = await self._queue.get()

                # 终止信号
                if event is None:
                    logger.debug("收到终止信号，退出消费循环")
                    break

                await self._dispatch_event(event)

            except asyncio.CancelledError:
                logger.info("事件消费任务被取消")
                break
            except Exception:
                logger.exception("事件消费过程中发生异常")

        logger.info("事件消费循环已退出")

    async def _dispatch_event(self, event: EventMessage) -> None:
        """
        分发事件给所有订阅者（内部方法）

        Args:
            event: 待分发的事件消息
        """
        handlers = self._subscribers.get(event.event_type, set())

        if not handlers:
            logger.debug("事件类型 '%s' 无订阅者，跳过分发", event.event_type)
            return

        logger.debug(
            "分发事件: type=%s, subscribers=%d, correlation_id=%s",
            event.event_type,
            len(handlers),
            event.correlation_id,
        )

        # 并发执行所有处理器
        tasks = [asyncio.create_task(self._safe_call_handler(handler, event)) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _safe_call_handler(handler: EventHandler, event: EventMessage) -> None:
        """
        安全调用事件处理器（内部方法）

        捕获处理器中的异常，防止单个处理器失败影响其他处理器。

        Args:
            handler: 事件处理器
            event: 事件消息
        """
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "事件处理器执行失败: type=%s, handler=%s, correlation_id=%s",
                event.event_type,
                handler.__name__,
                event.correlation_id,
            )

    @property
    def is_running(self) -> bool:
        """事件总线是否正在运行"""
        return self._running

    @property
    def subscriber_count(self) -> int:
        """当前订阅者总数"""
        return sum(len(handlers) for handlers in self._subscribers.values())

    def list_event_types(self) -> List[str]:
        """列出所有已订阅的事件类型"""
        return list(self._subscribers.keys())


# 全局事件总线单例
event_bus = EventBus()