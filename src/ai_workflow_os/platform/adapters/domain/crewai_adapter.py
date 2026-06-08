"""
CrewAI适配器

提供CrewAI框架的Agent适配实现，支持CrewAI Crew/Agent的统一调用和管理。
"""

import logging
import time
from typing import Any

from .agent_adapter import AgentAdapter
from .enums import AdapterStatus, AdapterType

logger = logging.getLogger(__name__)


class CrewAIAgentAdapter(AgentAdapter):
    """CrewAI适配器

    封装CrewAI框架的Agent调用逻辑，支持Crew协作模式的Agent编排。

    Attributes:
        agent_reference: CrewAI Agent/Crew实例引用
        invocation_count: 累计调用次数
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """初始化CrewAI适配器

        Args:
            config: CrewAI Agent配置
        """
        super().__init__(config)
        self.agent_reference: Any | None = None
        self.invocation_count: int = 0

    @property
    def adapter_type(self) -> AdapterType:
        """获取适配器类型"""
        return AdapterType.CREWAI

    async def invoke(self, input_data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """调用CrewAI Agent

        Args:
            input_data: 输入数据，包含task等字段
            config: 调用级配置

        Returns:
            Agent执行结果

        Raises:
            RuntimeError: Agent未初始化或调用失败
        """
        if self.agent_reference is None:
            raise RuntimeError("CrewAI Agent未初始化，请先配置agent_reference")

        # 合并配置：调用级配置覆盖适配器默认配置
        merged_config = {**self.config, **config}

        start_time = time.monotonic()

        try:
            # TODO: 对接实际的CrewAI Crew/Agent调用
            # result = self.agent_reference.kickoff(input_data)
            result = {
                "output": f"CrewAI agent processed: {input_data.get('query', '')}",
                "config_used": merged_config,
            }

            elapsed_ms = (time.monotonic() - start_time) * 1000
            self.invocation_count += 1
            logger.info(
                "CrewAI Agent调用成功: invocation_count=%d, elapsed=%.2fms",
                self.invocation_count,
                elapsed_ms,
            )
            return result

        except Exception as exc:
            logger.error("CrewAI Agent调用失败: error_type=%s, detail=%s", type(exc).__name__, exc)
            raise RuntimeError(f"CrewAI Agent调用失败: {exc}") from exc

    async def health_check(self) -> bool:
        """执行健康检查

        Returns:
            适配器是否健康
        """
        try:
            is_healthy = self.agent_reference is not None
            self.status = AdapterStatus.ACTIVE if is_healthy else AdapterStatus.INACTIVE
            return is_healthy
        except Exception as exc:
            logger.error("CrewAI适配器健康检查失败: %s", exc)
            self.status = AdapterStatus.ERROR
            return False

    async def metrics(self) -> dict[str, Any]:
        """获取适配器运行指标

        Returns:
            包含调用次数、适配器类型和状态的指标字典
        """
        return {
            "adapter_type": self.adapter_type.value,
            "status": self.status.value,
            "invocation_count": self.invocation_count,
            "has_agent": self.agent_reference is not None,
        }

    async def shutdown(self) -> None:
        """关闭适配器，释放CrewAI Agent资源"""
        self.agent_reference = None
        self.status = AdapterStatus.INACTIVE
        logger.info("CrewAI适配器已关闭")
