"""
适配器领域层

定义Agent适配器相关的领域实体、抽象基类和枚举。
"""

from .adapter_invocation import AdapterInvocation
from .agent_adapter import AgentAdapter
from .autogen_adapter import AutoGenAdapter
from .crewai_adapter import CrewAIAgentAdapter
from .enums import AdapterStatus, AdapterType, InvocationStatus
from .langchain_adapter import LangChainAdapter
from .langgraph_adapter import LangGraphAdapter
from .mcp_adapter import MCPAdapter
