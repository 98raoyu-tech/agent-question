"""
事件中心枚举定义

定义事件类型、优先级、投递模式和事件存储状态等核心枚举。
"""

from enum import Enum


class EventType(str, Enum):
    """事件类型枚举

    覆盖智能体平台全生命周期事件：Agent、Workflow、Tool、Knowledge、Prompt、
    Evaluation、Approval、Cost、Security、System。
    """

    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_PUBLISHED = "agent_published"
    AGENT_DEPLOYED = "agent_deployed"
    AGENT_ROLLED_BACK = "agent_rolled_back"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TOOL_INVOKED = "tool_invoked"
    TOOL_FAILED = "tool_failed"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    KNOWLEDGE_PUBLISHED = "knowledge_published"
    PROMPT_UPDATED = "prompt_updated"
    PROMPT_RELEASED = "prompt_released"
    EVALUATION_COMPLETED = "evaluation_completed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    COST_THRESHOLD_EXCEEDED = "cost_threshold_exceeded"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_HEALTH_CHECK = "system_health_check"


class EventPriority(str, Enum):
    """事件优先级枚举

    数值越小优先级越低，CRITICAL 优先级最高。
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryMode(str, Enum):
    """投递模式枚举

    定义事件消息的投递语义保证级别。
    """

    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class EventStoreStatus(str, Enum):
    """事件存储状态枚举

    描述事件在存储中的生命周期阶段。
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    PURGED = "purged"


class EventMessageStatus(str, Enum):
    """事件消息状态枚举

    描述事件消息从发布到消费的完整生命周期。
    """

    PENDING = "pending"
    PUBLISHED = "published"
    CONSUMED = "consumed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class BrokerType(str, Enum):
    """消息代理类型枚举

    支持的事件总线后端类型。
    """

    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    IN_MEMORY = "in_memory"
