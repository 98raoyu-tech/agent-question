"""
适配器仓储实现

提供适配器实例和调用历史的内存存储实现，后续替换为数据库持久化。
"""

import logging

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.adapter_invocation import AdapterInvocation
from ..domain.agent_adapter import AgentAdapter

logger = logging.getLogger(__name__)


class AdapterRepository:
    """适配器仓储实现

    基于内存字典的仓储实现，管理适配器实例和调用历史。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._adapters: dict[str, AgentAdapter] = {}
        self._invocations: dict[str, AdapterInvocation] = {}

    # =========================================================================
    # 适配器管理
    # =========================================================================

    async def save_adapter(self, adapter_id: str, adapter: AgentAdapter) -> AgentAdapter:
        """保存适配器实例

        Args:
            adapter_id: 适配器标识
            adapter: 适配器实例

        Returns:
            保存后的适配器实例
        """
        self._adapters[adapter_id] = adapter
        logger.debug("适配器已保存: id=%s, type=%s", adapter_id, adapter.adapter_type.value)
        return adapter

    async def find_adapter_by_id(self, adapter_id: str) -> AgentAdapter | None:
        """根据ID查找适配器

        Args:
            adapter_id: 适配器标识

        Returns:
            适配器实例，未找到返回None
        """
        return self._adapters.get(adapter_id)

    async def find_all_adapters(
        self,
        filters: dict | None = None,
    ) -> list[tuple[str, AgentAdapter]]:
        """查询所有适配器

        Args:
            filters: 过滤条件

        Returns:
            适配器列表（id, adapter）元组
        """
        adapters = list(self._adapters.items())

        # 应用过滤条件
        if filters:
            if "adapter_type" in filters:
                adapters = [
                    (aid, a) for aid, a in adapters
                    if a.adapter_type.value == filters["adapter_type"]
                ]
            if "status" in filters:
                adapters = [
                    (aid, a) for aid, a in adapters
                    if a.status.value == filters["status"]
                ]

        return adapters

    async def delete_adapter(self, adapter_id: str) -> bool:
        """删除适配器

        Args:
            adapter_id: 适配器标识

        Returns:
            是否删除成功
        """
        if adapter_id not in self._adapters:
            return False

        del self._adapters[adapter_id]
        logger.debug("适配器已删除: id=%s", adapter_id)
        return True

    # =========================================================================
    # 调用记录管理
    # =========================================================================

    async def save_invocation(self, invocation: AdapterInvocation) -> AdapterInvocation:
        """保存调用记录

        Args:
            invocation: 调用记录实体

        Returns:
            保存后的调用记录
        """
        self._invocations[invocation.id] = invocation
        logger.debug("调用记录已保存: id=%s, agent_id=%s", invocation.id, invocation.agent_id)
        return invocation

    async def find_invocation_by_id(self, invocation_id: str) -> AdapterInvocation | None:
        """根据ID查找调用记录

        Args:
            invocation_id: 调用记录标识

        Returns:
            调用记录实体，未找到返回None
        """
        return self._invocations.get(invocation_id)

    async def find_all_invocations(
        self,
        pagination: PaginatedRequest,
        agent_id: str | None = None,
    ) -> PaginatedResponse[AdapterInvocation]:
        """分页查询调用记录

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤

        Returns:
            分页响应结果
        """
        invocations = [
            inv for inv in self._invocations.values()
            if not inv.is_deleted
        ]

        # Agent过滤
        if agent_id is not None:
            invocations = [inv for inv in invocations if inv.agent_id == agent_id]

        # 按创建时间倒序排列
        invocations.sort(key=lambda inv: inv.created_at, reverse=True)

        # 计算总数
        total = len(invocations)

        # 分页
        start = pagination.offset
        end = start + pagination.page_size
        page_items = invocations[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
