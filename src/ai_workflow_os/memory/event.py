"""
事件记忆存储模块

本模块实现了基于 Kafka 的事件溯源记忆存储，支持事件发布、订阅和回放。
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .base import MemoryEntry, MemoryStore

logger = logging.getLogger(__name__)


class EventMemoryStore(MemoryStore):
    """
    基于 Kafka 的事件记忆存储

    使用 Kafka 实现事件溯源，支持事件发布、订阅和历史回放。

    Attributes:
        producer: Kafka 生产者
        consumer: Kafka 消费者
        topic: Kafka 主题
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "memory-events",
        group_id: str = "memory-group",
    ):
        """
        初始化事件记忆存储

        Args:
            bootstrap_servers: Kafka 服务器地址
            topic: Kafka 主题
            group_id: 消费者组 ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: dict[str, Callable] = {}

    async def initialize(self) -> None:
        """
        初始化 Kafka 生产者和消费者

        创建 Kafka 连接并验证连接状态。
        """
        try:
            # 初始化生产者
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self.producer.start()

            # 初始化消费者
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
            )
            await self.consumer.start()

            logger.info("事件记忆存储初始化完成")

        except Exception as e:
            logger.error(f"事件记忆存储初始化失败: {e}")
            raise

    async def store(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """
        存储记忆条目（作为事件）

        Args:
            key: 记忆条目的唯一标识符
            value: 要存储的值
            metadata: 可选的元数据信息
        """
        await self.store_event(
            event_type="memory.store",
            payload={
                "key": key,
                "value": value,
                "metadata": metadata or {},
            },
            correlation_id=key,
        )

    async def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """
        检索记忆条目

        Args:
            key: 要检索的记忆条目标识符

        Returns:
            MemoryEntry 实例，如果不存在则返回 None
        """
        events = await self.query_events(correlation_id=key)
        if not events:
            return None

        # 获取最新的存储事件
        store_events = [e for e in events if e.get("event_type") == "memory.store"]
        if not store_events:
            return None

        latest_event = store_events[-1]
        payload = latest_event.get("payload", {})

        return MemoryEntry(
            key=key,
            value=payload.get("value"),
            metadata=payload.get("metadata", {}),
            created_at=datetime.fromisoformat(latest_event.get("timestamp", "")),
            updated_at=datetime.fromisoformat(latest_event.get("timestamp", "")),
        )

    async def search(self, query: str, top_k: int = 10) -> list[MemoryEntry]:
        """
        搜索记忆条目（基于事件内容）

        Args:
            query: 搜索查询字符串
            top_k: 返回的最大结果数量

        Returns:
            匹配的记忆条目列表
        """
        # 注意：Kafka 不适合复杂搜索，这里返回空列表
        # 实际应用中可以结合其他存储实现
        logger.warning("Kafka 事件存储不支持复杂搜索，建议使用其他存储实现")
        return []

    async def store_event(
        self,
        event_type: str,
        payload: dict,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        存储事件

        Args:
            event_type: 事件类型
            payload: 事件数据
            correlation_id: 关联 ID

        Returns:
            事件 ID
        """
        if not self.producer:
            raise RuntimeError("事件记忆存储未初始化，请先调用 initialize()")

        try:
            event_id = str(uuid.uuid4())
            event = {
                "event_id": event_id,
                "event_type": event_type,
                "payload": payload,
                "correlation_id": correlation_id or event_id,
                "timestamp": datetime.now().isoformat(),
            }

            await self.producer.send_and_wait(self.topic, value=event)

            logger.debug(f"事件已存储: {event_type}, ID: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"存储事件失败: {e}")
            raise

    async def query_events(self, correlation_id: str) -> list[dict]:
        """
        按关联 ID 查询事件

        Args:
            correlation_id: 关联 ID

        Returns:
            事件列表
        """
        if not self.consumer:
            raise RuntimeError("事件记忆存储未初始化，请先调用 initialize()")

        try:
            events = []

            # 从头开始消费消息
            await self.consumer.seek_to_beginning()

            # 设置超时时间
            timeout_ms = 5000

            async for message in self.consumer:
                event = message.value
                if event.get("correlation_id") == correlation_id:
                    events.append(event)

                # 检查是否超时
                if message.timestamp and (datetime.now().timestamp() * 1000 - message.timestamp) > timeout_ms:
                    break

            logger.debug(f"查询事件完成，关联 ID: {correlation_id}，结果数量: {len(events)}")
            return events

        except Exception as e:
            logger.error(f"查询事件失败: {e}")
            raise

    async def replay_events(
        self,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
    ) -> list[dict]:
        """
        事件回放

        Args:
            from_timestamp: 开始时间（ISO 格式）
            to_timestamp: 结束时间（ISO 格式）

        Returns:
            时间范围内的事件列表
        """
        if not self.consumer:
            raise RuntimeError("事件记忆存储未初始化，请先调用 initialize()")

        try:
            events = []

            # 从头开始消费消息
            await self.consumer.seek_to_beginning()

            async for message in self.consumer:
                event = message.value
                event_timestamp = event.get("timestamp", "")

                # 检查时间范围
                if from_timestamp and event_timestamp < from_timestamp:
                    continue
                if to_timestamp and event_timestamp > to_timestamp:
                    break

                events.append(event)

            logger.debug(f"事件回放完成，结果数量: {len(events)}")
            return events

        except Exception as e:
            logger.error(f"事件回放失败: {e}")
            raise

    async def subscribe_to_events(
        self,
        event_types: list[str],
        handler: Callable[[dict], None],
    ) -> None:
        """
        订阅特定类型事件

        Args:
            event_types: 事件类型列表
            handler: 事件处理函数
        """
        if not self.consumer:
            raise RuntimeError("事件记忆存储未初始化，请先调用 initialize()")

        try:
            # 注册处理器
            for event_type in event_types:
                self._handlers[event_type] = handler

            # 启动消费循环
            async for message in self.consumer:
                event = message.value
                event_type = event.get("event_type")

                if event_type in self._handlers:
                    await self._handlers[event_type](event)

        except Exception as e:
            logger.error(f"事件订阅失败: {e}")
            raise

    async def get_event_history(self, entity_id: str) -> list[dict]:
        """
        获取实体的事件历史

        Args:
            entity_id: 实体 ID

        Returns:
            实体相关的事件列表
        """
        return await self.query_events(correlation_id=entity_id)

    async def delete(self, key: str) -> None:
        """
        删除事件（标记删除）

        Args:
            key: 要删除的事件关联 ID
        """
        await self.store_event(
            event_type="memory.delete",
            payload={"key": key},
            correlation_id=key,
        )

    async def clear(self) -> None:
        """
        清空所有事件（标记清空）
        """
        await self.store_event(
            event_type="memory.clear",
            payload={},
        )

    async def close(self) -> None:
        """
        关闭 Kafka 连接
        """
        try:
            if self.producer:
                await self.producer.stop()
            if self.consumer:
                await self.consumer.stop()

            logger.info("事件记忆存储已关闭")

        except Exception as e:
            logger.error(f"关闭事件记忆存储失败: {e}")
            raise