"""
Agent通信实体

定义Agent间消息通信的核心领域实体，管理消息的发送、投递、已读和失败生命周期。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import CommunicationType, MessageStatus

ACTIVE_MESSAGE_STATES = {MessageStatus.SENT, MessageStatus.DELIVERED}


@dataclass
class AgentMessage(BaseEntity):
    """Agent消息实体

    表示Agent间的一条通信消息，包含发送方、接收方、消息类型、内容和完整投递状态追踪。

    Attributes:
        sender_agent_id: 发送方Agent标识
        receiver_agent_id: 接收方Agent标识
        communication_type: 通信类型
        subject: 消息主题
        content: 消息内容
        priority: 优先级（1-10，数值越大优先级越高）
        correlation_id: 关联ID，用于请求-响应配对
        status: 消息状态
        sent_at: 发送时间
        delivered_at: 投递时间
        read_at: 已读时间
        reply_to_id: 回复目标消息ID
    """

    sender_agent_id: str = ""
    receiver_agent_id: str = ""
    communication_type: CommunicationType = CommunicationType.REQUEST
    subject: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    correlation_id: Optional[str] = field(default=None)
    status: MessageStatus = MessageStatus.SENT
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = field(default=None)
    read_at: Optional[datetime] = field(default=None)
    reply_to_id: Optional[str] = field(default=None)

    def mark_delivered(self, operator: Optional[str] = None) -> None:
        """标记消息为已投递

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 消息状态不允许标记为已投递
        """
        if self.status not in {MessageStatus.SENT}:
            raise BusinessRuleViolationException(
                rule="MESSAGE_STATUS_TRANSITION",
                message=f"消息 [{self.id}] 当前状态为 {self.status.value}，无法标记为已投递",
            )
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
        self.touch(operator)

    def mark_read(self, operator: Optional[str] = None) -> None:
        """标记消息为已读

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 消息状态不允许标记为已读
        """
        if self.status not in {MessageStatus.SENT, MessageStatus.DELIVERED}:
            raise BusinessRuleViolationException(
                rule="MESSAGE_STATUS_TRANSITION",
                message=f"消息 [{self.id}] 当前状态为 {self.status.value}，无法标记为已读",
            )
        self.status = MessageStatus.READ
        self.read_at = datetime.now(timezone.utc)
        self.touch(operator)

    def mark_failed(self, error: str, operator: Optional[str] = None) -> None:
        """标记消息为投递失败

        Args:
            error: 错误描述
            operator: 操作者标识
        """
        self.status = MessageStatus.FAILED
        self.content["error"] = error
        self.touch(operator)

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """判断消息是否已超时

        Args:
            timeout_seconds: 超时时间（秒），默认300秒

        Returns:
            消息处于活跃状态且超过超时时间返回True
        """
        if self.status not in ACTIVE_MESSAGE_STATES:
            return False
        elapsed = (datetime.now(timezone.utc) - self.sent_at).total_seconds()
        return elapsed > timeout_seconds
