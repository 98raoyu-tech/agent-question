"""
事件消息实体

定义事件消息的核心领域实体，承载事件发布、消费、重试和死信队列的完整生命周期管理。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from ...common.base_entity import BaseEntity
from .enums import DeliveryMode, EventMessageStatus, EventPriority, EventType


@dataclass
class EventMessage(BaseEntity):
    """事件消息实体

    表示一条通过事件总线传输的事件消息，包含完整的发布、消费、重试和死信生命周期管理。

    Attributes:
        event_type: 事件类型
        priority: 事件优先级
        delivery_mode: 投递模式
        source: 事件来源标识
        destination: 事件目标标识
        payload: 事件负载数据
        headers: 事件头部元数据
        correlation_id: 关联ID，用于链路追踪
        status: 消息当前状态
        published_at: 发布时间
        consumed_at: 消费时间
        retry_count: 当前重试次数
        max_retries: 最大重试次数
        error_message: 最近一次错误信息
    """

    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    priority: EventPriority = EventPriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    source: str = ""
    destination: str = ""
    payload: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    correlation_id: str | None = field(default=None)
    status: EventMessageStatus = EventMessageStatus.PENDING
    published_at: datetime | None = field(default=None)
    consumed_at: datetime | None = field(default=None)
    retry_count: int = field(default=0)
    max_retries: int = field(default=3)
    error_message: str | None = field(default=None)

    def publish(self, operator: str | None = None) -> None:
        """标记事件为已发布

        Args:
            operator: 操作者标识
        """
        self.status = EventMessageStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.touch(operator)

    def consume(self, operator: str | None = None) -> None:
        """标记事件为已消费

        Args:
            operator: 操作者标识

        Raises:
            RuntimeError: 事件未处于PUBLISHED状态时抛出
        """
        if self.status != EventMessageStatus.PUBLISHED:
            raise RuntimeError(
                f"事件消息 [{self.id}] 当前状态为 [{self.status.value}]，无法消费"
            )
        self.status = EventMessageStatus.CONSUMED
        self.consumed_at = datetime.now(UTC)
        self.touch(operator)

    def fail(self, error: str, operator: str | None = None) -> None:
        """标记事件消费失败

        Args:
            error: 错误描述信息
            operator: 操作者标识
        """
        self.status = EventMessageStatus.FAILED
        self.error_message = error
        self.touch(operator)

    def retry(self, operator: str | None = None) -> bool:
        """尝试重试事件消费

        如果未超过最大重试次数，则增加重试计数并将状态重置为PUBLISHED。

        Args:
            operator: 操作者标识

        Returns:
            是否重试成功（未超过最大次数返回True）
        """
        if not self.is_retriable():
            return False

        self.retry_count += 1
        self.status = EventMessageStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.error_message = None
        self.touch(operator)
        return True

    def is_retriable(self) -> bool:
        """判断事件是否可以重试

        Returns:
            当重试次数未超过最大限制时返回True
        """
        return self.retry_count < self.max_retries

    def send_to_dead_letter(self, operator: str | None = None) -> None:
        """将事件移入死信队列

        当事件重试耗尽后调用，将状态标记为DEAD_LETTER。

        Args:
            operator: 操作者标识
        """
        self.status = EventMessageStatus.DEAD_LETTER
        self.touch(operator)
