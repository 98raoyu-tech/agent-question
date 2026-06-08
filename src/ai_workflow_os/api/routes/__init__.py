"""
路由模块 - API路由定义

包含工作流、Agent、记忆、工具、审核、认证等业务路由。
"""

from .workflow import router as workflow_router
from .agent import router as agent_router
from .memory import router as memory_router
from .tool import router as tool_router
from .approval import router as approval_router
from .auth import router as auth_router

__all__ = [
    "workflow_router",
    "agent_router",
    "memory_router",
    "tool_router",
    "approval_router",
    "auth_router",
]
