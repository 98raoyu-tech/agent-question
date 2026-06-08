"""
多智能体组织领域层

定义Agent注册表、消息通信、任务委托、团队管理和任务管理等核心领域实体与枚举。
"""

from .agent_communication import AgentMessage
from .agent_delegation import AgentDelegation
from .agent_registry import AgentRegistryEntry
from .agent_task import AgentTask
from .agent_team import AgentTeam
from .enums import (
    AgentOrgStatus,
    AgentRole,
    CommunicationType,
    MessageStatus,
    TaskStatus,
    TeamStatus,
)
