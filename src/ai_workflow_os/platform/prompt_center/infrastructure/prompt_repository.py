"""
Prompt仓储实现

提供Prompt模板实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.base_repository import BaseRepository
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


class PromptRepository(BaseRepository[PromptTemplate]):
    """Prompt仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._store: dict[str, PromptTemplate] = {}

    async def find_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[PromptTemplate]:
        """根据ID查找Prompt模板

        Args:
            entity_id: 模板标识
            tenant_id: 租户标识

        Returns:
            模板实体，未找到返回None
        """
        template = self._store.get(entity_id)

        if template is not None and tenant_id is not None and template.tenant_id != tenant_id:
            return None

        if template is not None and template.is_deleted:
            return None

        return template

    async def find_all(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[PromptTemplate]:
        """分页查询Prompt模板列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        templates = [t for t in self._store.values() if not t.is_deleted]

        if tenant_id is not None:
            templates = [t for t in templates if t.tenant_id == tenant_id]

        templates.sort(key=lambda t: t.created_at, reverse=True)

        total = len(templates)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = templates[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save(self, entity: PromptTemplate) -> PromptTemplate:
        """保存Prompt模板

        Args:
            entity: 模板实体

        Returns:
            保存后的模板实体
        """
        self._store[entity.id] = entity
        return entity

    async def delete(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """删除Prompt模板（软删除）

        Args:
            entity_id: 模板标识
            tenant_id: 租户标识

        Returns:
            是否删除成功
        """
        template = await self.find_by_id(entity_id, tenant_id)
        if template is None:
            return False

        template.mark_deleted()
        return True

    async def exists(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """检查Prompt模板是否存在

        Args:
            entity_id: 模板标识
            tenant_id: 租户标识

        Returns:
            是否存在
        """
        template = await self.find_by_id(entity_id, tenant_id)
        return template is not None

    async def count(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> int:
        """统计Prompt模板数量

        Args:
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            模板数量
        """
        templates = [t for t in self._store.values() if not t.is_deleted]

        if tenant_id is not None:
            templates = [t for t in templates if t.tenant_id == tenant_id]

        return len(templates)
