"""
Agent Registry枚举定义

定义Agent注册相关的枚举类型，包括注册状态、框架类型和健康状态。
"""

from enum import Enum


class AgentRegistryStatus(str, Enum):
    """Agent注册状态枚举"""

    REGISTERED = "registered"
    """已注册状态"""

    ACTIVE = "active"
    """活跃状态"""

    INACTIVE = "inactive"
    """未激活状态"""

    DEPRECATED = "deprecated"
    """已废弃状态"""

    SUSPENDED = "suspended"
    """已暂停状态"""


class FrameworkType(str, Enum):
    """Agent框架类型枚举"""

    LANGCHAIN = "langchain"
    """LangChain框架"""

    LANGGRAPH = "langgraph"
    """LangGraph框架"""

    CREWAI = "crewai"
    """CrewAI框架"""

    AUTOGEN = "autogen"
    """AutoGen框架"""

    MCP = "mcp"
    """MCP框架"""

    CUSTOM = "custom"
    """自定义框架"""


class HealthStatus(str, Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    """健康状态"""

    UNHEALTHY = "unhealthy"
    """不健康状态"""

    DEGRADED = "degraded"
    """降级状态"""

    UNKNOWN = "unknown"
    """未知状态"""
