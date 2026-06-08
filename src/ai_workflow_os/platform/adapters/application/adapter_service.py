"""
适配器服务

提供适配器注册、Agent调用、健康检查等业务逻辑。
"""

import logging
import time
from typing import Any

from ...common.exceptions import (
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.adapter_invocation import AdapterInvocation
from ..domain.agent_adapter import AgentAdapter
from ..domain.autogen_adapter import AutoGenAdapter
from ..domain.crewai_adapter import CrewAIAgentAdapter
from ..domain.enums import AdapterType, InvocationStatus
from ..domain.langchain_adapter import LangChainAdapter
from ..domain.langgraph_adapter import LangGraphAdapter
from ..domain.mcp_adapter import MCPAdapter
from ..infrastructure.adapter_repository import AdapterRepository

logger = logging.getLogger(__name__)

# 适配器类型到具体实现类的映射
_ADAPTER_TYPE_MAP: dict[AdapterType, type[AgentAdapter]] = {
    AdapterType.LANGCHAIN: LangChainAdapter,
    AdapterType.LANGGRAPH: LangGraphAdapter,
    AdapterType.CREWAI: CrewAIAgentAdapter,
    AdapterType.AUTOGEN: AutoGenAdapter,
    AdapterType.MCP: MCPAdapter,
}


class AdapterService:
    """适配器业务服务

    提供适配器的完整生命周期管理，包括注册、调用、查询和健康检查。

    Attributes:
        repository: 适配器仓储实例
    """

    def __init__(self, repository: AdapterRepository) -> None:
        """初始化适配器服务

        Args:
            repository: 适配器仓储实例
        """
        self.repository = repository

    async def register_adapter(
        self,
        adapter_type: AdapterType,
        config: dict[str, Any],
        operator: str | None = None,
    ) -> AgentAdapter:
        """注册新的适配器

        根据适配器类型创建对应的适配器实例并持久化。

        Args:
            adapter_type: 适配器类型
            config: 适配器配置
            operator: 操作者标识

        Returns:
            创建后的适配器实例

        Raises:
            ValidationException: 不支持的适配器类型
        """
        adapter_class = _ADAPTER_TYPE_MAP.get(adapter_type)
        if adapter_class is None:
            raise ValidationException(
                message=f"不支持的适配器类型: {adapter_type.value}",
                errors=[f"支持的类型: {[t.value for t in AdapterType]}"],
            )

        # 创建适配器实例
        adapter = adapter_class(config)
        adapter.created_by = operator
        adapter.updated_by = operator

        # 保存到仓储
        saved_adapter = await self.repository.save_adapter(
            adapter_id=adapter.id,
            adapter=adapter,
        )
        logger.info(
            "适配器注册成功: id=%s, type=%s, operator=%s",
            saved_adapter.id,
            adapter_type.value,
            operator,
        )

        return saved_adapter

    async def invoke_agent(
        self,
        adapter_id: str,
        agent_id: str,
        input_data: dict[str, Any],
        config: dict[str, Any] | None = None,
        operator: str | None = None,
    ) -> AdapterInvocation:
        """通过适配器调用Agent

        Args:
            adapter_id: 适配器标识
            agent_id: Agent标识
            input_data: 输入数据
            config: 调用级配置
            operator: 操作者标识

        Returns:
            调用记录

        Raises:
            ResourceNotFoundException: 适配器不存在
        """
        # 查找适配器
        adapter = await self.repository.find_adapter_by_id(adapter_id)
        if adapter is None:
            raise ResourceNotFoundException(resource_type="Adapter", resource_id=adapter_id)

        # 创建调用记录
        invocation = AdapterInvocation(
            adapter_type=adapter.adapter_type,
            agent_id=agent_id,
            input_data=input_data,
            status=InvocationStatus.RUNNING,
            created_by=operator,
            updated_by=operator,
        )
        invocation.started_at = invocation.created_at
        await self.repository.save_invocation(invocation)

        # 执行调用
        start_time = time.monotonic()

        try:
            output_data = await adapter.invoke(input_data, config or {})

            # 标记成功
            elapsed_ms = (time.monotonic() - start_time) * 1000
            invocation.complete(output_data, operator)
            invocation.latency_ms = elapsed_ms
            logger.info(
                "Agent调用成功: invocation_id=%s, adapter_id=%s, elapsed=%.2fms",
                invocation.id,
                adapter_id,
                elapsed_ms,
            )

        except Exception as exc:
            # 标记失败
            elapsed_ms = (time.monotonic() - start_time) * 1000
            invocation.fail(str(exc), operator)
            invocation.latency_ms = elapsed_ms
            logger.error(
                "Agent调用失败: invocation_id=%s, adapter_id=%s, error=%s",
                invocation.id,
                adapter_id,
                exc,
            )

        # 保存调用结果
        await self.repository.save_invocation(invocation)
        return invocation

    async def get_adapter(self, adapter_id: str) -> AgentAdapter:
        """获取适配器详情

        Args:
            adapter_id: 适配器标识

        Returns:
            适配器实例

        Raises:
            ResourceNotFoundException: 适配器不存在
        """
        adapter = await self.repository.find_adapter_by_id(adapter_id)
        if adapter is None:
            raise ResourceNotFoundException(resource_type="Adapter", resource_id=adapter_id)
        return adapter

    async def list_adapters(
        self,
        filters: dict | None = None,
    ) -> list[tuple[str, AgentAdapter]]:
        """查询适配器列表

        Args:
            filters: 过滤条件

        Returns:
            适配器列表
        """
        return await self.repository.find_all_adapters(filters)

    async def get_invocation(self, invocation_id: str) -> AdapterInvocation:
        """获取调用记录详情

        Args:
            invocation_id: 调用记录标识

        Returns:
            调用记录实体

        Raises:
            ResourceNotFoundException: 调用记录不存在
        """
        invocation = await self.repository.find_invocation_by_id(invocation_id)
        if invocation is None:
            raise ResourceNotFoundException(
                resource_type="Invocation",
                resource_id=invocation_id,
            )
        return invocation

    async def list_invocations(
        self,
        agent_id: str | None = None,
        pagination: PaginatedRequest | None = None,
    ) -> PaginatedResponse[AdapterInvocation]:
        """分页查询调用记录

        Args:
            agent_id: Agent标识过滤
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        if pagination is None:
            pagination = PaginatedRequest()

        return await self.repository.find_all_invocations(pagination, agent_id)

    async def check_health(self, adapter_id: str) -> bool:
        """检查适配器健康状态

        Args:
            adapter_id: 适配器标识

        Returns:
            是否健康

        Raises:
            ResourceNotFoundException: 适配器不存在
        """
        adapter = await self.get_adapter(adapter_id)
        is_healthy = await adapter.health_check()
        logger.info(
            "适配器健康检查: id=%s, healthy=%s, status=%s",
            adapter_id,
            is_healthy,
            adapter.status.value,
        )
        return is_healthy
