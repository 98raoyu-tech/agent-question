"""
核心模块

提供平台运行所需的基础组件，包括配置管理、异常体系、
组件注册中心和事件总线。
"""

from .config import Settings, settings
from .events import EventBus, EventMessage, event_bus
from .exceptions import (
    AgentException,
    AgentScheduleException,
    AgentTimeoutException,
    CircuitBreakerOpenException,
    HumanApprovalTimeoutException,
    MemoryException,
    PolicyViolationException,
    ToolException,
    ToolNotFoundException,
    ToolPermissionDeniedException,
    WorkflowException,
    WorkflowExecutionException,
    WorkflowNotFoundException,
    WorkflowOSException,
)
from .registry import Registry, registry

__all__ = [
    # 配置管理
    "Settings",
    "settings",
    # 事件总线
    "EventBus",
    "EventMessage",
    "event_bus",
    # 异常体系
    "WorkflowOSException",
    "AgentException",
    "AgentScheduleException",
    "AgentTimeoutException",
    "WorkflowException",
    "WorkflowNotFoundException",
    "WorkflowExecutionException",
    "ToolException",
    "ToolNotFoundException",
    "ToolPermissionDeniedException",
    "MemoryException",
    "PolicyViolationException",
    "CircuitBreakerOpenException",
    "HumanApprovalTimeoutException",
    # 组件注册中心
    "Registry",
    "registry",
]