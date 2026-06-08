"""
Agent 抽象基类

定义所有 Agent 的通用接口、枚举类型和数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


# ==================== 枚举定义 ====================

class AgentType(str, Enum):
    """Agent 类型枚举"""
    PLANNER = "planner"
    EXECUTOR = "executor"
    TOOL = "tool"
    MEMORY = "memory"
    REVIEWER = "reviewer"
    POLICY = "policy"
    RECOVERY = "recovery"
    DEPLOYMENT = "deployment"
    SECURITY = "security"


class AgentStatus(str, Enum):
    """Agent 状态枚举"""
    IDLE = "idle"
    SCHEDULING = "scheduling"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYED = "destroyed"


# ==================== 数据类定义 ====================

@dataclass
class AgentTask:
    """Agent 任务数据结构

    Attributes:
        task_id: 任务唯一标识
        task_type: 任务类型
        payload: 任务负载数据
        priority: 任务优先级（数值越小优先级越高）
        timeout: 超时时间（秒）
        correlation_id: 关联 ID，用于追踪任务链
    """
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: int = 300
    correlation_id: str = ""


@dataclass
class AgentResult:
    """Agent 执行结果数据结构

    Attributes:
        task_id: 对应的任务 ID
        agent_id: 执行 Agent 的 ID
        status: 执行状态
        output: 输出结果
        error: 错误信息（如果执行失败）
        duration_ms: 执行耗时（毫秒）
        tokens_used: 使用的 token 数量
    """
    task_id: str = ""
    agent_id: str = ""
    status: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    tokens_used: int = 0


# ==================== 抽象基类 ====================

class BaseAgent(ABC):
    """Agent 抽象基类

    所有具体 Agent 必须继承此类并实现抽象方法。

    Attributes:
        agent_id: Agent 唯一标识
        agent_name: Agent 名称
        agent_type: Agent 类型
        status: Agent 当前状态
        context: Agent 上下文信息
        created_at: 创建时间
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "",
        agent_type: AgentType = AgentType.EXECUTOR,
    ) -> None:
        """初始化 Agent

        Args:
            agent_id: Agent 唯一标识，为空时自动生成
            agent_name: Agent 名称
            agent_type: Agent 类型
        """
        self.agent_id: str = agent_id or uuid.uuid4().hex[:12]
        self.agent_name: str = agent_name
        self.agent_type: AgentType = agent_type
        self.status: AgentStatus = AgentStatus.IDLE
        self.context: dict[str, Any] = {}
        self.created_at: datetime = datetime.now(timezone.utc)

    # ==================== 抽象方法 ====================

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """执行任务

        Args:
            task: 待执行的任务

        Returns:
            执行结果
        """
        ...

    @abstractmethod
    async def pause(self) -> None:
        """暂停 Agent 执行"""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """恢复 Agent 执行"""
        ...

    @abstractmethod
    async def checkpoint(self) -> dict[str, Any]:
        """保存检查点

        Returns:
            检查点状态数据
        """
        ...

    @abstractmethod
    async def restore(self, state: dict[str, Any]) -> None:
        """从检查点恢复状态

        Args:
            state: 检查点状态数据
        """
        ...

    # ==================== 生命周期钩子 ====================

    async def on_create(self) -> None:
        """Agent 创建时的生命周期钩子

        子类可重写此方法以执行初始化逻辑。
        """
        pass

    async def on_destroy(self) -> None:
        """Agent 销毁时的生命周期钩子

        子类可重写此方法以执行清理逻辑。
        """
        self.status = AgentStatus.DESTROYED

    # ==================== 事件发送 ====================

    async def emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """发送事件到事件总线

        Args:
            event_type: 事件类型
            payload: 事件负载数据
        """
        event = {
            "event_type": event_type,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        # TODO: 集成实际的事件总线（如 Kafka）
        print(f"[Event] {event_type}: {event}")

    # ==================== 表示方法 ====================

    def __repr__(self) -> str:
        """返回 Agent 的字符串表示"""
        return (
            f"<{self.__class__.__name__}("
            f"id={self.agent_id}, "
            f"name={self.agent_name}, "
            f"type={self.agent_type.value}, "
            f"status={self.status.value}"
            f")>"
        )