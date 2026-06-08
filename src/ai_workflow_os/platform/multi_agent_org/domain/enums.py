"""
多智能体组织枚举定义

定义Agent角色、组织状态、通信类型、任务状态和团队状态等核心枚举。
"""

from enum import Enum


class AgentRole(str, Enum):
    """Agent角色枚举

    定义多智能体协作中的角色分工。
    """

    PM = "pm"
    ARCHITECT = "architect"
    BACKEND_DEV = "backend_dev"
    FRONTEND_DEV = "frontend_dev"
    QA = "qa"
    REVIEWER = "reviewer"
    DEVOPS = "devops"
    DATA_ANALYST = "data_analyst"
    SECURITY = "security"


class AgentOrgStatus(str, Enum):
    """Agent组织状态枚举

    描述Agent在组织协作中的运行状态。
    """

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class CommunicationType(str, Enum):
    """通信类型枚举

    定义Agent间消息通信的类型。
    """

    REQUEST = "request"
    RESPONSE = "response"
    DELEGATION = "delegation"
    BROADCAST = "broadcast"
    ESCALATION = "escalation"


class TaskStatus(str, Enum):
    """任务状态枚举

    描述任务从创建到完成的完整生命周期。
    """

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TeamStatus(str, Enum):
    """团队状态枚举

    描述团队的生命周期阶段。
    """

    FORMING = "forming"
    ACTIVE = "active"
    DISBANDED = "disbanded"


class MessageStatus(str, Enum):
    """消息状态枚举

    描述Agent间消息的投递生命周期。
    """

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
