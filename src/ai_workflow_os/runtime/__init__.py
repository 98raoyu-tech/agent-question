"""
Runtime 运行时模块

提供 AI 系统的核心运行时能力，包括：
- HarnessRuntime: 运行时内核，统一调度和管理所有组件
- AgentScheduler: 多 Agent 集群调度器
- LifecycleManager: Agent 生命周期管理器
- ContextManager: Prompt 上下文管理器
- CircuitBreaker: 熔断器，防止级联故障
- ModelFallback: 模型降级策略管理
"""

from .circuit_breaker import CircuitBreaker, CircuitState, circuit_breaker
from .context import ContextManager, ContextWindow
from .fallback import ModelConfig, ModelFallback
from .harness import HarnessRuntime
from .lifecycle import (
    AgentLifecyclePhase,
    AgentLifecycleState,
    LifecycleManager,
    PhaseTransition,
)
from .scheduler import AgentScheduler, SchedulingStrategy


# ==================== 导出列表 ====================

__all__ = [
    # 运行时内核
    "HarnessRuntime",

    # 调度器
    "AgentScheduler",
    "SchedulingStrategy",

    # 生命周期管理
    "LifecycleManager",
    "AgentLifecyclePhase",
    "AgentLifecycleState",
    "PhaseTransition",

    # 上下文管理
    "ContextManager",
    "ContextWindow",

    # 熔断器
    "CircuitBreaker",
    "CircuitState",
    "circuit_breaker",

    # 模型降级
    "ModelFallback",
    "ModelConfig",
]
