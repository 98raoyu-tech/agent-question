"""
LangChain适配器

提供LangChain框架的Agent适配实现，支持LangChain Agent的统一调用和管理。
"""

import logging
import time
from typing import Any

from .agent_adapter import AgentAdapter
from .enums import AdapterStatus, AdapterType

logger = logging.getLogger(__name__)


class LangChainAdapter(AgentAdapter):
    """LangChain适配器

    封装LangChain框架的Agent调用逻辑，提供统一的适配器接口。

    Attributes:
        agent_reference: LangChain Agent实例引用
        invocation_count: 累计调用次数
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """初始化LangChain适配器

        Args:
            config: LangChain Agent配置
        """
        super().__init__(config)
        self.agent_reference: Any | None = None
        self.invocation_count: int = 0

    @property
    def adapter_type(self) -> AdapterType:
        """获取适配器类型"""
        return AdapterType.LANGCHAIN

    async def invoke(self, input_data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """调用LangChain Agent

        Args:
            input_data: 输入数据，包含query等字段
            config: 调用级配置

        Returns:
            Agent执行结果

        Raises:
            RuntimeError: Agent未初始化或调用失败
        """
        if self.agent_reference is None:
            raise RuntimeError("LangChain Agent未初始化，请先配置agent_reference")

        # 合并配置：调用级配置覆盖适配器默认配置
        merged_config = {**self.config, **config}

        start_time = time.monotonic()

        try:
            # TODO: 对接实际的LangChain Agent调用链
            # result = self.agent_reference.invoke(input_data, config=merged_config)
            result = {
                "output": f"LangChain agent processed: {input_data.get('query', '')}",
                "config_used": merged_config,
            }

            elapsed_ms = (time.monotonic() - start_time) * 1000
            self.invocation_count += 1
            logger.info(
                "LangChain Agent调用成功: invocation_count=%d, elapsed=%.2fms",
                self.invocation_count,
                elapsed_ms,
            )
            return result

        except Exception as exc:
            logger.error("LangChain Agent调用失败: error_type=%s, detail=%s", type(exc).__name__, exc)
            raise RuntimeError(f"LangChain Agent调用失败: {exc}") from exc

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
            logger.error("LangChain适配器健康检查失败: %s", exc)
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
        """关闭适配器，释放LangChain Agent资源"""
        self.agent_reference = None
        self.status = AdapterStatus.INACTIVE
        logger.info("LangChain适配器已关闭")
