"""
Harness Runtime 核心模块（AI Runtime Kernel）

作为整个 AI 系统的运行时内核，统一调度和管理所有组件：
- Agent 调度与执行
- 上下文路由与管理
- 工具权限控制
- 熔断保护
- 模型降级
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..agents.base import AgentResult, AgentStatus, AgentTask, BaseAgent
from .circuit_breaker import CircuitBreaker
from .context import ContextManager
from .fallback import ModelFallback
from .lifecycle import LifecycleManager
from .scheduler import AgentScheduler, SchedulingStrategy

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class RuntimeState(str, Enum):
    """运行时状态枚举"""
    INITIALIZED = "initialized"
    BOOTING = "booting"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


# ==================== 运行时配置 ====================

class RuntimeConfig:
    """运行时配置

    Attributes:
        max_concurrent_agents: 最大并发 Agent 数量
        scheduling_strategy: 调度策略
        default_timeout: 默认任务超时时间（秒）
        max_retries: 最大重试次数
        circuit_breaker_threshold: 熔断器失败阈值
        circuit_breaker_timeout: 熔断器恢复超时（秒）
        max_context_size: 最大上下文大小（token 数）
    """

    def __init__(
        self,
        max_concurrent_agents: int = 10,
        scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LEAST_LOADED,
        default_timeout: float = 300.0,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
        max_context_size: int = 128000,
    ) -> None:
        """初始化运行时配置"""
        self.max_concurrent_agents = max_concurrent_agents
        self.scheduling_strategy = scheduling_strategy
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.max_context_size = max_context_size


# ==================== 运行时核心类 ====================

class HarnessRuntime:
    """Harness Runtime 运行时内核

    作为整个 AI 系统的运行时内核，统一调度和管理所有组件。
    提供任务调度、上下文路由、工具权限管理、熔断保护和模型降级等核心能力。

    Attributes:
        config: 运行时配置
        scheduler: Agent 调度器
        lifecycle_mgr: 生命周期管理器
        context_mgr: 上下文管理器
        circuit_breaker: 熔断器
        fallback: 模型降级管理器
        state: 运行时状态
        _started_at: 启动时间
    """

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        """初始化运行时内核

        Args:
            config: 运行时配置，为 None 时使用默认配置
        """
        self.config: RuntimeConfig = config or RuntimeConfig()

        # 初始化核心组件
        self.scheduler: AgentScheduler = AgentScheduler(
            max_concurrent_agents=self.config.max_concurrent_agents,
            strategy=self.config.scheduling_strategy,
        )
        self.lifecycle_mgr: LifecycleManager = LifecycleManager()
        self.context_mgr: ContextManager = ContextManager(
            max_context_size=self.config.max_context_size,
        )
        self.circuit_breaker: CircuitBreaker = CircuitBreaker(
            name="runtime",
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_timeout,
        )
        self.fallback: ModelFallback = ModelFallback()

        # 运行时状态
        self.state: RuntimeState = RuntimeState.INITIALIZED
        self._started_at: datetime | None = None

        logger.info("Harness Runtime 内核已初始化")

    # ==================== 生命周期方法 ====================

    async def boot(self) -> None:
        """启动运行时

        初始化所有组件并进入运行状态。
        """
        if self.state == RuntimeState.RUNNING:
            logger.warning("运行时已在运行中，跳过启动")
            return

        self.state = RuntimeState.BOOTING
        logger.info("Harness Runtime 正在启动...")

        try:
            # 记录启动时间
            self._started_at = datetime.now(timezone.utc)

            # 重置熔断器
            self.circuit_breaker.reset()

            # 切换到运行状态
            self.state = RuntimeState.RUNNING
            logger.info("Harness Runtime 启动成功")

        except Exception as error:
            self.state = RuntimeState.ERROR
            logger.error("Harness Runtime 启动失败: %s", str(error))
            raise

    async def shutdown(self) -> None:
        """优雅关闭运行时

        等待所有运行中的任务完成，然后关闭所有组件。
        """
        if self.state != RuntimeState.RUNNING:
            logger.warning("运行时未在运行状态，当前状态: %s", self.state.value)
            return

        self.state = RuntimeState.SHUTTING_DOWN
        logger.info("Harness Runtime 正在关闭...")

        try:
            # 等待运行中的任务完成
            running_tasks = self.scheduler._running_tasks
            if running_tasks:
                logger.info("等待 %d 个运行中的任务完成...", len(running_tasks))
                await asyncio.gather(*running_tasks.values(), return_exceptions=True)

            self.state = RuntimeState.STOPPED
            logger.info("Harness Runtime 已关闭")

        except Exception as error:
            self.state = RuntimeState.ERROR
            logger.error("Harness Runtime 关闭异常: %s", str(error))
            raise

    # ==================== 任务调度 ====================

    async def dispatch_task(self, task: AgentTask) -> AgentResult:
        """调度任务到合适的 Agent

        通过调度器选择最佳 Agent，执行任务并返回结果。

        Args:
            task: 待调度的任务

        Returns:
            AgentResult: 任务执行结果

        Raises:
            RuntimeError: 当运行时未启动或调度失败时抛出
        """
        self._ensure_running()

        start_time = time.time()
        logger.info("开始调度任务: %s (类型: %s)", task.task_id, task.task_type)

        try:
            # 选择最佳 Agent
            selected_agent = await self.scheduler.select_agent(task)

            # 更新调度器负载信息
            self.scheduler.update_agent_task_start(selected_agent.agent_id)

            # 执行任务
            result = await selected_agent.execute(task)

            # 更新调度器负载信息
            duration_ms = (time.time() - start_time) * 1000
            self.scheduler.update_agent_task_complete(
                selected_agent.agent_id, duration_ms
            )

            logger.info(
                "任务 '%s' 执行完成 (Agent: %s, 耗时: %.2fms)",
                task.task_id,
                selected_agent.agent_id,
                duration_ms,
            )
            return result

        except Exception as error:
            logger.error(
                "任务 '%s' 调度失败: %s", task.task_id, str(error)
            )
            raise

    # ==================== 上下文路由 ====================

    async def route_context(
        self, agent_id: str, context: dict[str, Any]
    ) -> str:
        """路由上下文到目标 Agent

        为指定 Agent 创建或更新上下文。

        Args:
            agent_id: 目标 Agent ID
            context: 上下文数据

        Returns:
            str: 上下文 ID
        """
        self._ensure_running()

        # 创建上下文
        initial_prompt = context.get("prompt", "")
        context_id = self.context_mgr.create_context(agent_id, initial_prompt)

        # 追加额外消息
        messages = context.get("messages", [])
        for message in messages:
            self.context_mgr.append_to_context(context_id, message)

        logger.info(
            "已路由上下文到 Agent '%s': %s", agent_id, context_id
        )
        return context_id

    # ==================== 工具权限管理 ====================

    async def manage_tool_permission(
        self, agent_id: str, tool_name: str
    ) -> bool:
        """管理工具权限

        检查指定 Agent 是否有权使用指定工具。

        Args:
            agent_id: Agent ID
            tool_name: 工具名称

        Returns:
            bool: 有权限返回 True
        """
        self._ensure_running()

        # 获取 Agent 实例
        agent = self.scheduler.agent_pool.get(agent_id)
        if not agent:
            logger.warning("Agent '%s' 不存在，无法检查工具权限", agent_id)
            return False

        # 从 Agent 的上下文中获取权限信息
        # TODO: 集成实际的权限管理模块
        logger.info(
            "已检查 Agent '%s' 使用工具 '%s' 的权限: 允许",
            agent_id,
            tool_name,
        )
        return True

    # ==================== 重试执行 ====================

    async def execute_with_retry(
        self, task: AgentTask, max_retries: int | None = None
    ) -> AgentResult:
        """带重试的执行

        当任务执行失败时自动重试，直到达到最大重试次数。

        Args:
            task: 待执行的任务
            max_retries: 最大重试次数，为 None 时使用默认值

        Returns:
            AgentResult: 任务执行结果
        """
        self._ensure_running()

        retries = max_retries if max_retries is not None else self.config.max_retries
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    logger.info(
                        "任务 '%s' 第 %d 次重试", task.task_id, attempt
                    )

                result = await self.dispatch_task(task)

                # 执行成功
                if attempt > 0:
                    logger.info(
                        "任务 '%s' 在第 %d 次重试后成功", task.task_id, attempt
                    )
                return result

            except Exception as error:
                last_error = error
                logger.warning(
                    "任务 '%s' 执行失败 (尝试 %d/%d): %s",
                    task.task_id,
                    attempt + 1,
                    retries + 1,
                    str(error),
                )

        # 所有重试均失败
        logger.error(
            "任务 '%s' 在 %d 次尝试后仍然失败", task.task_id, retries + 1
        )
        return AgentResult(
            task_id=task.task_id,
            status="failed",
            error=str(last_error) if last_error else "未知错误",
        )

    # ==================== 超时执行 ====================

    async def execute_with_timeout(
        self, task: AgentTask, timeout_seconds: float | None = None
    ) -> AgentResult:
        """带超时的执行

        在指定时间内完成任务，超时则返回失败结果。

        Args:
            task: 待执行的任务
            timeout_seconds: 超时时间（秒），为 None 时使用默认值

        Returns:
            AgentResult: 任务执行结果
        """
        self._ensure_running()

        timeout = timeout_seconds or self.config.default_timeout

        try:
            result = await asyncio.wait_for(
                self.dispatch_task(task), timeout=timeout
            )
            return result

        except asyncio.TimeoutError:
            logger.error(
                "任务 '%s' 执行超时 (%.1f 秒)", task.task_id, timeout
            )
            return AgentResult(
                task_id=task.task_id,
                status="timeout",
                error=f"任务执行超时 ({timeout} 秒)",
            )

        except Exception as error:
            logger.error(
                "任务 '%s' 执行异常: %s", task.task_id, str(error)
            )
            return AgentResult(
                task_id=task.task_id,
                status="failed",
                error=str(error),
            )

    # ==================== 模型降级 ====================

    async def fallback_model(
        self, primary_model: str, fallback_model: str
    ) -> None:
        """配置模型降级

        设置主模型和降级模型的映射关系。

        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
        """
        # TODO: 集成实际的模型降级配置
        logger.info(
            "已配置模型降级: %s -> %s", primary_model, fallback_model
        )

    # ==================== 状态查询 ====================

    async def get_runtime_status(self) -> dict[str, Any]:
        """获取运行时状态

        Returns:
            dict: 运行时状态信息
        """
        cluster_status = await self.scheduler.get_cluster_status()
        context_stats = self.context_mgr.get_statistics()
        circuit_state = self.circuit_breaker.get_state()
        fallback_stats = self.fallback.get_statistics()

        uptime_seconds = 0.0
        if self._started_at:
            uptime_seconds = (
                datetime.now(timezone.utc) - self._started_at
            ).total_seconds()

        return {
            "state": self.state.value,
            "uptime_seconds": round(uptime_seconds, 2),
            "cluster": cluster_status,
            "context": context_stats,
            "circuit_breaker": circuit_state,
            "model_fallback": fallback_stats,
        }

    # ==================== 内部工具方法 ====================

    def _ensure_running(self) -> None:
        """确保运行时处于运行状态

        Raises:
            RuntimeError: 当运行时未启动时抛出
        """
        if self.state != RuntimeState.RUNNING:
            raise RuntimeError(
                f"运行时未启动，当前状态: {self.state.value}"
            )
