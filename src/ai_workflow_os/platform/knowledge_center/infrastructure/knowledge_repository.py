"""
知识仓储实现

提供知识源和文档实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.knowledge_chunk import KnowledgeChunk
from ..domain.knowledge_document import KnowledgeDocument
from ..domain.knowledge_source import KnowledgeSource

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """知识仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    TODO: 后续集成向量数据库（如Milvus/Qdrant）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._sources: dict[str, KnowledgeSource] = {}
        self._documents: dict[str, KnowledgeDocument] = {}
        self._chunks: dict[str, KnowledgeChunk] = {}

    # =========================================================================
    # 知识源操作
    # =========================================================================

    async def find_source_by_id(self, source_id: str) -> Optional[KnowledgeSource]:
        """根据ID查找知识源

        Args:
            source_id: 知识源标识

        Returns:
            知识源实体，未找到返回None
        """
        source = self._sources.get(source_id)
        if source is not None and source.is_deleted:
            return None
        return source

    async def find_all_sources(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[KnowledgeSource]:
        """分页查询知识源列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        sources = [s for s in self._sources.values() if not s.is_deleted]

        if tenant_id is not None:
            sources = [s for s in sources if s.tenant_id == tenant_id]

        sources.sort(key=lambda s: s.created_at, reverse=True)

        total = len(sources)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = sources[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_source(self, source: KnowledgeSource) -> KnowledgeSource:
        """保存知识源

        Args:
            source: 知识源实体

        Returns:
            保存后的知识源实体
        """
        self._sources[source.id] = source
        return source

    # =========================================================================
    # 文档操作
    # =========================================================================

    async def find_document_by_id(self, document_id: str) -> Optional[KnowledgeDocument]:
        """根据ID查找文档

        Args:
            document_id: 文档标识

        Returns:
            文档实体，未找到返回None
        """
        document = self._documents.get(document_id)
        if document is not None and document.is_deleted:
            return None
        return document

    async def find_documents_by_source(
        self,
        source_id: str,
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[KnowledgeDocument]:
        """查询知识源下的文档列表

        Args:
            source_id: 知识源标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        documents = [
            d for d in self._documents.values()
            if d.source_id == source_id and not d.is_deleted
        ]

        documents.sort(key=lambda d: d.created_at, reverse=True)

        total = len(documents)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = documents[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        """保存文档

        Args:
            document: 文档实体

        Returns:
            保存后的文档实体
        """
        self._documents[document.id] = document
        return document

    # =========================================================================
    # 切片操作
    # =========================================================================

    async def save_chunks(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        """批量保存切片

        Args:
            chunks: 切片列表

        Returns:
            保存后的切片列表
        """
        for chunk in chunks:
            self._chunks[chunk.id] = chunk
        return chunks

    async def find_chunks_by_document(self, document_id: str) -> list[KnowledgeChunk]:
        """查询文档下的切片列表

        Args:
            document_id: 文档标识

        Returns:
            切片列表
        """
        chunks = [c for c in self._chunks.values() if c.document_id == document_id]
        chunks.sort(key=lambda c: c.chunk_index)
        return chunks
