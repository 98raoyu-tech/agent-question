"""
领域事件基类

定义领域事件的公共结构，支持事件溯源和事件驱动架构。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EventStatus(str, Enum):
    """事件状态枚举"""

    PENDING = "pending"
    PUBLISHED = "published"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class BaseEvent:
    """领域事件基类

    所有领域事件必须继承此类，提供统一的事件标识、时间戳和元数据。

    Attributes:
        event_id: 事件唯一标识
        event_type: 事件类型标识符
        aggregate_id: 聚合根标识
        aggregate_type: 聚合根类型
        tenant_id: 租户标识
        occurred_at: 事件发生时间（UTC）
        published_at: 事件发布时间（UTC）
        status: 事件状态
        metadata: 事件元数据
        payload: 事件负载数据
        correlation_id: 关联ID，用于链路追踪
        causation_id: 因果ID，用于事件溯源
    """

    event_type: str
    aggregate_id: str
    aggregate_type: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    tenant_id: Optional[str] = field(default=None)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = field(default=None)
    status: EventStatus = field(default=EventStatus.PENDING)
    metadata: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = field(default=None)
    causation_id: Optional[str] = field(default=None)

    def mark_published(self) -> None:
        """标记事件为已发布"""
        self.status = EventStatus.PUBLISHED
        self.published_at = datetime.now(timezone.utc)

    def mark_processed(self) -> None:
        """标记事件为已处理"""
        self.status = EventStatus.PROCESSED

    def mark_failed(self, error: Optional[str] = None) -> None:
        """标记事件为处理失败

        Args:
            error: 错误信息
        """
        self.status = EventStatus.FAILED
        if error:
            self.metadata["error"] = error
