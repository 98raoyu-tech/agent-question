"""
Multi-Agent 集群调度器

负责 Agent 集群的任务调度，支持多种调度策略：
- round_robin: 轮询调度
- least_loaded: 最小负载优先
- capability_match: 能力匹配度优先
- priority: 任务优先级优先
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..agents.base import AgentResult, AgentStatus, AgentTask, BaseAgent

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class SchedulingStrategy(str, Enum):
    """调度策略枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_MATCH = "capability_match"
    PRIORITY = "priority"


# ==================== 数据类定义 ====================

@dataclass
class AgentLoadInfo:
    """Agent 负载信息

    Attributes:
        agent_id: Agent 唯一标识
        current_tasks: 当前正在执行的任务数
        total_completed: 累计完成任务数
        avg_duration_ms: 平均执行时长（毫秒）
        last_active_at: 最后活跃时间戳
    """
    agent_id: str = ""
    current_tasks: int = 0
    total_completed: int = 0
    avg_duration_ms: float = 0.0
    last_active_at: float = field(default_factory=time.time)


# ==================== 调度器核心类 ====================

class AgentScheduler:
    """Multi-Agent 集群调度器

    负责 Agent 集群的任务调度，根据不同的调度策略将任务分配给最合适的 Agent。

    Attributes:
        agent_pool: Agent 池，键为 agent_id
        task_queue: 任务优先队列
        max_concurrent_agents: 最大并发 Agent 数量
        strategy: 调度策略
        _running_tasks: 正在运行的任务映射
        _agent_load: Agent 负载信息映射
        _round_robin_index: 轮询调度索引
    """

    def __init__(
        self,
        max_concurrent_agents: int = 10,
        strategy: SchedulingStrategy = SchedulingStrategy.LEAST_LOADED,
    ) -> None:
        """初始化调度器

        Args:
            max_concurrent_agents: 最大并发 Agent 数量
            strategy: 调度策略
        """
        self.agent_pool: dict[str, BaseAgent] = {}
        self.task_queue: asyncio.PriorityQueue[tuple[int, str, AgentTask]] = (
            asyncio.PriorityQueue()
        )
        self.max_concurrent_agents: int = max_concurrent_agents
        self.strategy: SchedulingStrategy = strategy
        self._running_tasks: dict[str, asyncio.Task[AgentResult]] = {}
        self._agent_load: dict[str, AgentLoadInfo] = {}
        self._round_robin_index: int = 0
        logger.info(
            "调度器已初始化 (策略: %s, 最大并发: %d)",
            strategy.value,
            max_concurrent_agents,
        )

    # ==================== Agent 注册与注销 ====================

    async def register_agent(self, agent: BaseAgent) -> None:
        """注册 Agent 到调度池

        Args:
            agent: 待注册的 Agent 实例
        """
        if agent.agent_id in self.agent_pool:
            logger.warning("Agent '%s' 已存在于调度池中，跳过注册", agent.agent_id)
            return

        self.agent_pool[agent.agent_id] = agent
        self._agent_load[agent.agent_id] = AgentLoadInfo(agent_id=agent.agent_id)
        logger.info(
            "已注册 Agent: %s (类型: %s)", agent.agent_id, agent.agent_type.value
        )

    async def unregister_agent(self, agent_id: str) -> None:
        """从调度池移除 Agent

        Args:
            agent_id: 待移除的 Agent ID
        """
        if agent_id not in self.agent_pool:
            logger.warning("Agent '%s' 不存在于调度池中，无法移除", agent_id)
            return

        # 等待该 Agent 的所有运行任务完成
        if agent_id in self._running_tasks:
            running_task = self._running_tasks[agent_id]
            if not running_task.done():
                logger.info("等待 Agent '%s' 的运行任务完成...", agent_id)
                try:
                    await asyncio.wait_for(running_task, timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning("Agent '%s' 的运行任务超时，强制取消", agent_id)
                    running_task.cancel()

            del self._running_tasks[agent_id]

        del self.agent_pool[agent_id]
        del self._agent_load[agent_id]
        logger.info("已移除 Agent: %s", agent_id)

    # ==================== 任务调度 ====================

    async def schedule(self, task: AgentTask) -> str:
        """调度任务到合适的 Agent

        Args:
            task: 待调度的任务

        Returns:
            str: 被选中的 Agent ID

        Raises:
            RuntimeError: 当没有可用的 Agent 时抛出
        """
        # 选择最佳 Agent
        selected_agent = await self.select_agent(task)
        logger.info(
            "任务 '%s' 已调度至 Agent '%s' (策略: %s)",
            task.task_id,
            selected_agent.agent_id,
            self.strategy.value,
        )
        return selected_agent.agent_id

    async def select_agent(self, task: AgentTask) -> BaseAgent:
        """根据任务类型和负载选择最佳 Agent

        Args:
            task: 待调度的任务

        Returns:
            BaseAgent: 选中的 Agent 实例

        Raises:
            RuntimeError: 当没有可用的 Agent 时抛出
        """
        if not self.agent_pool:
            raise RuntimeError("调度池中没有可用的 Agent")

        # 过滤出空闲或运行中的 Agent
        available_agents = [
            agent
            for agent in self.agent_pool.values()
            if agent.status != AgentStatus.DESTROYED
        ]

        if not available_agents:
            raise RuntimeError("没有可用的 Agent（所有 Agent 均已销毁）")

        # 根据调度策略选择 Agent
        strategy_handlers = {
            SchedulingStrategy.ROUND_ROBIN: self._select_round_robin,
            SchedulingStrategy.LEAST_LOADED: self._select_least_loaded,
            SchedulingStrategy.CAPABILITY_MATCH: self._select_by_capability,
            SchedulingStrategy.PRIORITY: self._select_by_priority,
        }

        handler = strategy_handlers.get(self.strategy)
        if not handler:
            raise ValueError(f"未知的调度策略: {self.strategy.value}")

        return handler(task, available_agents)

    # ==================== 调度策略实现 ====================

    def _select_round_robin(
        self, task: AgentTask, available_agents: list[BaseAgent]
    ) -> BaseAgent:
        """轮询调度策略

        Args:
            task: 待调度的任务
            available_agents: 可用 Agent 列表

        Returns:
            BaseAgent: 选中的 Agent
        """
        index = self._round_robin_index % len(available_agents)
        selected = available_agents[index]
        self._round_robin_index = index + 1
        return selected

    def _select_least_loaded(
        self, task: AgentTask, available_agents: list[BaseAgent]
    ) -> BaseAgent:
        """最小负载调度策略

        选择当前负载最低的 Agent。

        Args:
            task: 待调度的任务
            available_agents: 可用 Agent 列表

        Returns:
            BaseAgent: 选中的 Agent
        """
        selected = min(
            available_agents,
            key=lambda agent: self._calculate_agent_load(agent),
        )
        return selected

    def _select_by_capability(
        self, task: AgentTask, available_agents: list[BaseAgent]
    ) -> BaseAgent:
        """能力匹配调度策略

        根据任务类型与 Agent 能力的匹配度选择最佳 Agent。

        Args:
            task: 待调度的任务
            available_agents: 可用 Agent 列表

        Returns:
            BaseAgent: 选中的 Agent
        """
        scored_agents = [
            (agent, self._match_task_to_agent(task, agent))
            for agent in available_agents
        ]

        # 按匹配度降序排列
        scored_agents.sort(key=lambda item: item[1], reverse=True)
        return scored_agents[0][0]

    def _select_by_priority(
        self, task: AgentTask, available_agents: list[BaseAgent]
    ) -> BaseAgent:
        """优先级调度策略

        优先选择空闲状态的 Agent，其次选择负载最低的 Agent。

        Args:
            task: 待调度的任务
            available_agents: 可用 Agent 列表

        Returns:
            BaseAgent: 选中的 Agent
        """
        # 优先选择空闲 Agent
        idle_agents = [
            agent for agent in available_agents if agent.status == AgentStatus.IDLE
        ]

        if idle_agents:
            return min(
                idle_agents,
                key=lambda agent: self._calculate_agent_load(agent),
            )

        # 无空闲 Agent 时选择负载最低的
        return min(
            available_agents,
            key=lambda agent: self._calculate_agent_load(agent),
        )

    # ==================== 负载计算 ====================

    def _calculate_agent_load(self, agent: BaseAgent) -> float:
        """计算 Agent 负载

        基于当前任务数和平均执行时长综合计算负载分数。

        Args:
            agent: 目标 Agent

        Returns:
            float: 负载分数（越低越好）
        """
        load_info = self._agent_load.get(agent.agent_id)
        if not load_info:
            return 0.0

        # 负载分数 = 当前任务数 * 10 + 平均耗时权重
        task_weight = load_info.current_tasks * 10.0
        duration_weight = load_info.avg_duration_ms / 1000.0

        return task_weight + duration_weight

    def _match_task_to_agent(self, task: AgentTask, agent: BaseAgent) -> float:
        """任务与 Agent 匹配度评分

        根据任务类型和 Agent 类型计算匹配度。

        Args:
            task: 待调度的任务
            agent: 目标 Agent

        Returns:
            float: 匹配度分数（越高越好）
        """
        # 任务类型与 Agent 类型的匹配映射
        type_match_map: dict[str, list[str]] = {
            "planning": ["planner"],
            "execution": ["executor"],
            "review": ["reviewer"],
            "memory": ["memory"],
            "policy": ["policy"],
            "recovery": ["recovery"],
            "deployment": ["deployment"],
            "security": ["security"],
        }

        expected_types = type_match_map.get(task.task_type, [])
        agent_type_value = agent.agent_type.value

        # 完全匹配得 100 分
        if agent_type_value in expected_types:
            return 100.0

        # 空闲状态加分 50 分
        base_score = 50.0 if agent.status == AgentStatus.IDLE else 0.0

        # 负载越低加分越多（最高 30 分）
        load = self._calculate_agent_load(agent)
        load_score = max(0.0, 30.0 - load)

        return base_score + load_score

    # ==================== 负载信息更新 ====================

    def update_agent_task_start(self, agent_id: str) -> None:
        """更新 Agent 任务开始状态

        Args:
            agent_id: Agent ID
        """
        load_info = self._agent_load.get(agent_id)
        if load_info:
            load_info.current_tasks += 1
            load_info.last_active_at = time.time()

    def update_agent_task_complete(
        self, agent_id: str, duration_ms: float
    ) -> None:
        """更新 Agent 任务完成状态

        Args:
            agent_id: Agent ID
            duration_ms: 任务执行耗时（毫秒）
        """
        load_info = self._agent_load.get(agent_id)
        if not load_info:
            return

        load_info.current_tasks = max(0, load_info.current_tasks - 1)
        load_info.total_completed += 1
        load_info.last_active_at = time.time()

        # 更新平均执行时长（滑动平均）
        if load_info.total_completed == 1:
            load_info.avg_duration_ms = duration_ms
        else:
            alpha = 0.3
            load_info.avg_duration_ms = (
                alpha * duration_ms + (1 - alpha) * load_info.avg_duration_ms
            )

    # ==================== 集群状态 ====================

    async def get_cluster_status(self) -> dict[str, Any]:
        """获取集群状态

        Returns:
            dict: 集群状态信息，包括各 Agent 状态和负载统计
        """
        agents_info: list[dict[str, Any]] = []

        for agent_id, agent in self.agent_pool.items():
            load_info = self._agent_load.get(agent_id, AgentLoadInfo())
            agents_info.append({
                "agent_id": agent_id,
                "agent_type": agent.agent_type.value,
                "status": agent.status.value,
                "current_tasks": load_info.current_tasks,
                "total_completed": load_info.total_completed,
                "avg_duration_ms": round(load_info.avg_duration_ms, 2),
            })

        return {
            "total_agents": len(self.agent_pool),
            "max_concurrent": self.max_concurrent_agents,
            "strategy": self.strategy.value,
            "running_tasks": len(self._running_tasks),
            "agents": agents_info,
        }
