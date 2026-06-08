"""
Agent仓储实现

提供Agent实体的内存存储实现，后续替换为数据库持久化。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ...common.base_repository import BaseRepository
from ..domain.agent_definition import AgentDefinition

logger = logging.getLogger(__name__)


class AgentRepository(BaseRepository[AgentDefinition]):
    """Agent仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._store: dict[str, AgentDefinition] = {}

    async def find_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentDefinition]:
        """根据ID查找Agent

        Args:
            entity_id: Agent标识
            tenant_id: 租户标识

        Returns:
            Agent实体，未找到返回None
        """
        agent = self._store.get(entity_id)

        # 检查租户隔离
        if agent is not None and tenant_id is not None and agent.tenant_id != tenant_id:
            return None

        # 检查软删除
        if agent is not None and agent.is_deleted:
            return None

        return agent

    async def find_all(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[AgentDefinition]:
        """分页查询Agent列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        # 过滤未删除的Agent
        agents = [
            agent for agent in self._store.values()
            if not agent.is_deleted
        ]

        # 租户过滤
        if tenant_id is not None:
            agents = [a for a in agents if a.tenant_id == tenant_id]

        # 应用过滤条件
        if filters:
            if "status" in filters:
                agents = [a for a in agents if a.status.value == filters["status"]]
            if "agent_type" in filters:
                agents = [a for a in agents if a.agent_type.value == filters["agent_type"]]
            if "search" in filters and filters["search"]:
                search_term = filters["search"].lower()
                agents = [
                    a for a in agents
                    if search_term in a.name.lower() or search_term in a.description.lower()
                ]

        # 排序
        if pagination.sort_by and hasattr(AgentDefinition, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            agents.sort(key=lambda a: getattr(a, pagination.sort_by, ""), reverse=reverse)
        else:
            agents.sort(key=lambda a: a.created_at, reverse=True)

        # 计算总数
        total = len(agents)

        # 分页
        start = pagination.offset
        end = start + pagination.page_size
        page_items = agents[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save(self, entity: AgentDefinition) -> AgentDefinition:
        """保存Agent

        Args:
            entity: Agent实体

        Returns:
            保存后的Agent实体
        """
        self._store[entity.id] = entity
        logger.debug("Agent已保存: id=%s", entity.id)
        return entity

    async def delete(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """删除Agent（软删除）

        Args:
            entity_id: Agent标识
            tenant_id: 租户标识

        Returns:
            是否删除成功
        """
        agent = await self.find_by_id(entity_id, tenant_id)
        if agent is None:
            return False

        agent.mark_deleted()
        logger.debug("Agent已删除: id=%s", entity_id)
        return True

    async def exists(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """检查Agent是否存在

        Args:
            entity_id: Agent标识
            tenant_id: 租户标识

        Returns:
            是否存在
        """
        agent = await self.find_by_id(entity_id, tenant_id)
        return agent is not None

    async def count(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> int:
        """统计Agent数量

        Args:
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            Agent数量
        """
        agents = [a for a in self._store.values() if not a.is_deleted]

        if tenant_id is not None:
            agents = [a for a in agents if a.tenant_id == tenant_id]

        return len(agents)
