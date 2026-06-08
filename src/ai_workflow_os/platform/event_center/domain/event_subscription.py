"""
事件订阅实体

定义事件订阅的核心领域实体，管理订阅者的事件类型注册、回调配置和投递统计。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from ...common.base_entity import BaseEntity
from .enums import DeliveryMode, EventType


@dataclass
class EventSubscription(BaseEntity):
    """事件订阅实体

    描述一个事件订阅关系，包含订阅者信息、关注的事件类型列表、
    过滤条件和投递统计。

    Attributes:
        name: 订阅名称
        description: 订阅描述
        event_types: 订阅的事件类型列表
        subscriber_id: 订阅者标识
        callback_url: 回调地址
        is_active: 是否激活
        filter_expression: 过滤表达式（JSON格式）
        delivery_mode: 投递模式
        created_by: 创建者标识
        last_delivered_at: 最近一次投递时间
        delivery_count: 累计投递次数
        failure_count: 累计失败次数
    """

    name: str = ""
    description: str = ""
    event_types: list[EventType] = field(default_factory=list)
    subscriber_id: str = ""
    callback_url: str = ""
    is_active: bool = True
    filter_expression: dict = field(default_factory=dict)
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    created_by: str | None = field(default=None)
    last_delivered_at: datetime | None = field(default=None)
    delivery_count: int = field(default=0)
    failure_count: int = field(default=0)

    def activate(self, operator: str | None = None) -> None:
        """激活订阅

        Args:
            operator: 操作者标识
        """
        self.is_active = True
        self.touch(operator)

    def deactivate(self, operator: str | None = None) -> None:
        """停用订阅

        Args:
            operator: 操作者标识
        """
        self.is_active = False
        self.touch(operator)

    def record_delivery(self, success: bool, operator: str | None = None) -> None:
        """记录一次投递结果

        Args:
            success: 投递是否成功
            operator: 操作者标识
        """
        self.delivery_count += 1
        self.last_delivered_at = datetime.now(UTC)

        if not success:
            self.failure_count += 1

        self.touch(operator)
