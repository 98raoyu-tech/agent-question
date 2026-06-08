"""
Agent 生命周期管理模块

管理每个 Agent 从创建到销毁的完整生命周期，支持：
- 生命周期阶段管理（创建、调度、上下文加载、工具执行等）
- 检查点创建与恢复
- 状态追踪与历史记录
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..agents.base import AgentStatus, AgentType, BaseAgent

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class AgentLifecyclePhase(str, Enum):
    """Agent 生命周期阶段枚举"""
    CREATE = "create"
    SCHEDULE = "schedule"
    LOAD_CONTEXT = "load_context"
    TOOL_EXECUTION = "tool_execution"
    MEMORY_UPDATE = "memory_update"
    CHECKPOINT = "checkpoint"
    RETRY_ROLLBACK = "retry_rollback"
    DESTROY = "destroy"


# ==================== 数据类定义 ====================

@dataclass
class PhaseTransition:
    """阶段转换记录

    Attributes:
        from_phase: 来源阶段
        to_phase: 目标阶段
        timestamp: 转换时间戳
        metadata: 附加元数据
    """
    from_phase: AgentLifecyclePhase | None
    to_phase: AgentLifecyclePhase
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentLifecycleState:
    """Agent 生命周期状态

    Attributes:
        agent_id: Agent 唯一标识
        current_phase: 当前生命周期阶段
        history: 阶段转换历史记录
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    agent_id: str = ""
    current_phase: AgentLifecyclePhase = AgentLifecyclePhase.CREATE
    history: list[PhaseTransition] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== 生命周期管理器 ====================

class LifecycleManager:
    """Agent 生命周期管理器

    管理每个 Agent 从创建到销毁的完整生命周期，支持状态追踪、
    检查点创建与恢复。

    Attributes:
        agents_state: Agent 生命周期状态映射，键为 agent_id
        checkpoints: 检查点存储，键为 agent_id，值为检查点数据映射
        _agents: Agent 实例映射
    """

    def __init__(self) -> None:
        """初始化生命周期管理器"""
        self.agents_state: dict[str, AgentLifecycleState] = {}
        self.checkpoints: dict[str, dict[str, dict[str, Any]]] = {}
        self._agents: dict[str, BaseAgent] = {}
        logger.info("生命周期管理器已初始化")

    # ==================== 阶段转换 ====================

    def _transition_phase(
        self,
        agent_id: str,
        target_phase: AgentLifecyclePhase,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """执行阶段转换

        Args:
            agent_id: Agent ID
            target_phase: 目标阶段
            metadata: 附加元数据
        """
        state = self.agents_state.get(agent_id)
        if not state:
            logger.warning("Agent '%s' 的生命周期状态不存在", agent_id)
            return

        # 记录阶段转换
        transition = PhaseTransition(
            from_phase=state.current_phase,
            to_phase=target_phase,
            metadata=metadata or {},
        )

        state.history.append(transition)
        state.current_phase = target_phase
        state.updated_at = datetime.now(timezone.utc)

        logger.info(
            "Agent '%s' 生命周期转换: %s -> %s",
            agent_id,
            transition.from_phase.value if transition.from_phase else "None",
            target_phase.value,
        )

    # ==================== 生命周期方法 ====================

    async def create_agent(
        self, agent_type: AgentType, config: dict[str, Any] | None = None
    ) -> BaseAgent:
        """创建 Agent

        根据 Agent 类型创建对应的 Agent 实例，并初始化其生命周期状态。

        Args:
            agent_type: Agent 类型
            config: Agent 配置参数

        Returns:
            BaseAgent: 创建的 Agent 实例

        Raises:
            ValueError: 当 Agent 类型不支持时抛出
        """
        # 延迟导入避免循环依赖
        from ..agents.deployment_agent import DeploymentAgent
        from ..agents.executor import ExecutorAgent
        from ..agents.memory_agent import MemoryAgent
        from ..agents.planner import PlannerAgent
        from ..agents.policy_agent import PolicyAgent
        from ..agents.recovery_agent import RecoveryAgent
        from ..agents.reviewer import ReviewerAgent
        from ..agents.security_agent import SecurityAgent

        # Agent 类型与实现类的映射
        agent_class_map: dict[AgentType, type[BaseAgent]] = {
            AgentType.PLANNER: PlannerAgent,
            AgentType.EXECUTOR: ExecutorAgent,
            AgentType.REVIEWER: ReviewerAgent,
            AgentType.MEMORY: MemoryAgent,
            AgentType.POLICY: PolicyAgent,
            AgentType.RECOVERY: RecoveryAgent,
            AgentType.DEPLOYMENT: DeploymentAgent,
            AgentType.SECURITY: SecurityAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"不支持的 Agent 类型: {agent_type.value}")

        # 创建 Agent 实例
        agent_config = config or {}
        agent = agent_class(
            agent_id=agent_config.get("agent_id", ""),
            agent_name=agent_config.get("agent_name", f"{agent_type.value}_agent"),
            agent_type=agent_type,
        )

        # 初始化生命周期状态
        self.agents_state[agent.agent_id] = AgentLifecycleState(
            agent_id=agent.agent_id,
            current_phase=AgentLifecyclePhase.CREATE,
        )
        self.checkpoints[agent.agent_id] = {}
        self._agents[agent.agent_id] = agent

        # 执行创建钩子
        await agent.on_create()

        logger.info(
            "已创建 Agent: %s (类型: %s)", agent.agent_id, agent_type.value
        )
        return agent

    async def schedule_agent(self, agent_id: str) -> None:
        """调度 Agent

        将 Agent 从创建阶段转入调度阶段。

        Args:
            agent_id: Agent ID
        """
        self._transition_phase(agent_id, AgentLifecyclePhase.SCHEDULE)

    async def load_context(
        self, agent_id: str, context: dict[str, Any]
    ) -> None:
        """加载上下文

        为 Agent 加载执行所需的上下文信息。

        Args:
            agent_id: Agent ID
            context: 上下文数据
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.context.update(context)

        self._transition_phase(
            agent_id,
            AgentLifecyclePhase.LOAD_CONTEXT,
            metadata={"context_keys": list(context.keys())},
        )

    async def execute_tools(
        self, agent_id: str, tools: list[str]
    ) -> None:
        """执行工具

        标记 Agent 进入工具执行阶段。

        Args:
            agent_id: Agent ID
            tools: 工具名称列表
        """
        self._transition_phase(
            agent_id,
            AgentLifecyclePhase.TOOL_EXECUTION,
            metadata={"tools": tools},
        )

    async def update_memory(
        self, agent_id: str, memory_data: dict[str, Any]
    ) -> None:
        """更新记忆

        标记 Agent 进入记忆更新阶段。

        Args:
            agent_id: Agent ID
            memory_data: 记忆数据
        """
        self._transition_phase(
            agent_id,
            AgentLifecyclePhase.MEMORY_UPDATE,
            metadata={"memory_keys": list(memory_data.keys())},
        )

    # ==================== 检查点管理 ====================

    async def checkpoint(self, agent_id: str) -> str:
        """创建检查点

        保存 Agent 当前状态的快照，用于后续恢复。

        Args:
            agent_id: Agent ID

        Returns:
            str: 检查点 ID

        Raises:
            ValueError: 当 Agent 不存在时抛出
        """
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' 不存在")

        # 获取 Agent 的检查点数据
        checkpoint_data = await agent.checkpoint()

        # 生成检查点 ID
        checkpoint_id = uuid.uuid4().hex[:12]

        # 保存检查点
        if agent_id not in self.checkpoints:
            self.checkpoints[agent_id] = {}

        self.checkpoints[agent_id][checkpoint_id] = {
            "agent_id": agent_id,
            "phase": self.agents_state[agent_id].current_phase.value,
            "agent_state": checkpoint_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 记录检查点阶段
        self._transition_phase(
            agent_id,
            AgentLifecyclePhase.CHECKPOINT,
            metadata={"checkpoint_id": checkpoint_id},
        )

        logger.info(
            "已为 Agent '%s' 创建检查点: %s", agent_id, checkpoint_id
        )
        return checkpoint_id

    async def restore_from_checkpoint(
        self, agent_id: str, checkpoint_id: str
    ) -> None:
        """从检查点恢复

        将 Agent 恢复到指定检查点的状态。

        Args:
            agent_id: Agent ID
            checkpoint_id: 检查点 ID

        Raises:
            ValueError: 当 Agent 或检查点不存在时抛出
        """
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' 不存在")

        agent_checkpoints = self.checkpoints.get(agent_id, {})
        checkpoint_data = agent_checkpoints.get(checkpoint_id)
        if not checkpoint_data:
            raise ValueError(
                f"检查点 '{checkpoint_id}' 不存在于 Agent '{agent_id}'"
            )

        # 恢复 Agent 状态
        await agent.restore(checkpoint_data.get("agent_state", {}))

        # 记录回滚阶段
        self._transition_phase(
            agent_id,
            AgentLifecyclePhase.RETRY_ROLLBACK,
            metadata={
                "checkpoint_id": checkpoint_id,
                "restored_from": checkpoint_data.get("timestamp", ""),
            },
        )

        logger.info(
            "已从检查点 '%s' 恢复 Agent '%s'", checkpoint_id, agent_id
        )

    # ==================== 销毁 ====================

    async def destroy_agent(self, agent_id: str) -> None:
        """销毁 Agent

        执行 Agent 的销毁钩子并清理相关资源。

        Args:
            agent_id: Agent ID
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning("Agent '%s' 不存在，无法销毁", agent_id)
            return

        # 执行销毁钩子
        await agent.on_destroy()

        # 记录销毁阶段
        self._transition_phase(agent_id, AgentLifecyclePhase.DESTROY)

        # 清理资源
        del self._agents[agent_id]
        if agent_id in self.checkpoints:
            del self.checkpoints[agent_id]

        logger.info("已销毁 Agent: %s", agent_id)

    # ==================== 状态查询 ====================

    def get_agent_state(self, agent_id: str) -> AgentLifecycleState | None:
        """获取 Agent 生命周期状态

        Args:
            agent_id: Agent ID

        Returns:
            AgentLifecycleState: 生命周期状态，不存在返回 None
        """
        return self.agents_state.get(agent_id)

    def get_all_states(self) -> dict[str, AgentLifecycleState]:
        """获取所有 Agent 的生命周期状态

        Returns:
            dict: 所有 Agent 的生命周期状态映射
        """
        return self.agents_state.copy()

    def get_agent_history(
        self, agent_id: str
    ) -> list[PhaseTransition]:
        """获取 Agent 的阶段转换历史

        Args:
            agent_id: Agent ID

        Returns:
            list: 阶段转换历史列表
        """
        state = self.agents_state.get(agent_id)
        return state.history if state else []
