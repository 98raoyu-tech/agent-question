"""
适配器枚举定义

定义Agent适配器相关的枚举类型，包括适配器类型、状态和调用状态。
"""

from enum import Enum


class AdapterType(str, Enum):
    """适配器类型枚举"""

    LANGCHAIN = "langchain"
    """LangChain适配器"""

    LANGGRAPH = "langgraph"
    """LangGraph适配器"""

    CREWAI = "crewai"
    """CrewAI适配器"""

    AUTOGEN = "autogen"
    """AutoGen适配器"""

    MCP = "mcp"
    """MCP（Model Context Protocol）适配器"""


class AdapterStatus(str, Enum):
    """适配器状态枚举"""

    ACTIVE = "active"
    """活跃状态"""

    INACTIVE = "inactive"
    """停用状态"""

    ERROR = "error"
    """异常状态"""


class InvocationStatus(str, Enum):
    """调用状态枚举"""

    PENDING = "pending"
    """待执行"""

    RUNNING = "running"
    """执行中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """执行失败"""

    TIMEOUT = "timeout"
    """执行超时"""
