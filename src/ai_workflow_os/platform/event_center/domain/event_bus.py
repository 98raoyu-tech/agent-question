"""
事件总线配置实体

定义事件总线的核心配置实体，管理消息代理连接、吞吐量控制和生命周期。
"""

from dataclasses import dataclass, field

from ...common.base_entity import BaseEntity
from .enums import BrokerType


@dataclass
class EventBusConfig(BaseEntity):
    """事件总线配置实体

    管理事件总线后端的连接配置、吞吐量限流和运行状态。

    Attributes:
        name: 总线名称
        broker_type: 消息代理类型
        connection_config: 连接配置（如broker地址、端口、认证信息等）
        is_active: 是否处于活跃状态
        topic_prefix: 主题前缀
        consumer_group: 消费者组标识
        max_throughput: 最大吞吐量（条/秒）
        current_throughput: 当前吞吐量（条/秒）
    """

    name: str = ""
    broker_type: BrokerType = BrokerType.IN_MEMORY
    connection_config: dict = field(default_factory=dict)
    is_active: bool = True
    topic_prefix: str = ""
    consumer_group: str = ""
    max_throughput: int = field(default=1000)
    current_throughput: int = field(default=0)

    def activate(self, operator: str | None = None) -> None:
        """激活事件总线

        Args:
            operator: 操作者标识
        """
        self.is_active = True
        self.touch(operator)

    def deactivate(self, operator: str | None = None) -> None:
        """停用事件总线

        Args:
            operator: 操作者标识
        """
        self.is_active = False
        self.touch(operator)

    def update_throughput(self, count: int, operator: str | None = None) -> None:
        """更新当前吞吐量计数

        Args:
            count: 当前吞吐量值
            operator: 操作者标识
        """
        self.current_throughput = count
        self.touch(operator)
