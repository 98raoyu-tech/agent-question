"""
工具仓储实现

提供工具定义实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.base_repository import BaseRepository
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.tool_definition import ToolDefinition

logger = logging.getLogger(__name__)


class ToolRepository(BaseRepository[ToolDefinition]):
    """工具仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._store: dict[str, ToolDefinition] = {}

    async def find_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[ToolDefinition]:
        """根据ID查找工具

        Args:
            entity_id: 工具标识
            tenant_id: 租户标识

        Returns:
            工具实体，未找到返回None
        """
        tool = self._store.get(entity_id)

        if tool is not None and tenant_id is not None and tool.tenant_id != tenant_id:
            return None

        if tool is not None and tool.is_deleted:
            return None

        return tool

    async def find_all(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[ToolDefinition]:
        """分页查询工具列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        tools = [t for t in self._store.values() if not t.is_deleted]

        if tenant_id is not None:
            tools = [t for t in tools if t.tenant_id == tenant_id]

        tools.sort(key=lambda t: t.created_at, reverse=True)

        total = len(tools)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = tools[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save(self, entity: ToolDefinition) -> ToolDefinition:
        """保存工具

        Args:
            entity: 工具实体

        Returns:
            保存后的工具实体
        """
        self._store[entity.id] = entity
        return entity

    async def delete(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """删除工具（软删除）

        Args:
            entity_id: 工具标识
            tenant_id: 租户标识

        Returns:
            是否删除成功
        """
        tool = await self.find_by_id(entity_id, tenant_id)
        if tool is None:
            return False

        tool.mark_deleted()
        return True

    async def exists(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """检查工具是否存在

        Args:
            entity_id: 工具标识
            tenant_id: 租户标识

        Returns:
            是否存在
        """
        tool = await self.find_by_id(entity_id, tenant_id)
        return tool is not None

    async def count(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> int:
        """统计工具数量

        Args:
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            工具数量
        """
        tools = [t for t in self._store.values() if not t.is_deleted]

        if tenant_id is not None:
            tools = [t for t in tools if t.tenant_id == tenant_id]

        return len(tools)
