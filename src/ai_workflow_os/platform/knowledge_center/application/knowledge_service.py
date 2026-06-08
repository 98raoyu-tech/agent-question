"""
知识服务

提供知识源和文档的CRUD、文档处理等业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import DocumentStatus
from ..domain.knowledge_document import KnowledgeDocument
from ..domain.knowledge_source import KnowledgeSource
from ..infrastructure.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识中心业务服务

    提供知识源和文档的完整生命周期管理。

    Attributes:
        repository: 知识仓储实例
    """

    def __init__(self, repository: KnowledgeRepository) -> None:
        """初始化知识服务

        Args:
            repository: 知识仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 知识源管理
    # =========================================================================

    async def create_source(
        self,
        source: KnowledgeSource,
        operator: Optional[str] = None,
    ) -> KnowledgeSource:
        """创建知识源

        Args:
            source: 知识源实体
            operator: 操作者标识

        Returns:
            创建后的知识源实体

        Raises:
            ValidationException: 名称为空
        """
        if not source.name or not source.name.strip():
            raise ValidationException(message="知识源名称不能为空")

        source.created_by = operator
        source.updated_by = operator

        saved_source = await self.repository.save_source(source)
        logger.info("知识源创建成功: id=%s, name=%s", saved_source.id, saved_source.name)

        return saved_source

    async def get_source(self, source_id: str) -> KnowledgeSource:
        """获取知识源详情

        Args:
            source_id: 知识源标识

        Returns:
            知识源实体

        Raises:
            ResourceNotFoundException: 知识源不存在
        """
        source = await self.repository.find_source_by_id(source_id)
        if source is None:
            raise ResourceNotFoundException(resource_type="知识源", resource_id=source_id)
        return source

    async def list_sources(
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
        return await self.repository.find_all_sources(pagination, tenant_id)

    async def delete_source(self, source_id: str, operator: Optional[str] = None) -> bool:
        """删除知识源（软删除）

        Args:
            source_id: 知识源标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 知识源不存在
        """
        source = await self.repository.find_source_by_id(source_id)
        if source is None:
            raise ResourceNotFoundException(resource_type="知识源", resource_id=source_id)

        source.mark_deleted(operator)
        await self.repository.save_source(source)
        logger.info("知识源删除成功: id=%s", source_id)

        return True

    # =========================================================================
    # 文档管理
    # =========================================================================

    async def create_document(
        self,
        document: KnowledgeDocument,
        operator: Optional[str] = None,
    ) -> KnowledgeDocument:
        """创建文档

        Args:
            document: 文档实体
            operator: 操作者标识

        Returns:
            创建后的文档实体

        Raises:
            ValidationException: 标题为空
            ResourceNotFoundException: 知识源不存在
        """
        if not document.title or not document.title.strip():
            raise ValidationException(message="文档标题不能为空")

        # 检查知识源是否存在
        source = await self.repository.find_source_by_id(document.source_id)
        if source is None:
            raise ResourceNotFoundException(resource_type="知识源", resource_id=document.source_id)

        document.created_by = operator
        document.updated_by = operator

        saved_document = await self.repository.save_document(document)

        # 更新知识源文档计数
        source.increment_document_count(operator)
        await self.repository.save_source(source)

        logger.info("文档创建成功: id=%s, title=%s", saved_document.id, saved_document.title)

        return saved_document

    async def get_document(self, document_id: str) -> KnowledgeDocument:
        """获取文档详情

        Args:
            document_id: 文档标识

        Returns:
            文档实体

        Raises:
            ResourceNotFoundException: 文档不存在
        """
        document = await self.repository.find_document_by_id(document_id)
        if document is None:
            raise ResourceNotFoundException(resource_type="文档", resource_id=document_id)
        return document

    async def list_documents(
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
        return await self.repository.find_documents_by_source(source_id, pagination)

    async def delete_document(self, document_id: str, operator: Optional[str] = None) -> bool:
        """删除文档（软删除）

        Args:
            document_id: 文档标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 文档不存在
        """
        document = await self.repository.find_document_by_id(document_id)
        if document is None:
            raise ResourceNotFoundException(resource_type="文档", resource_id=document_id)

        document.mark_deleted(operator)
        await self.repository.save_document(document)

        # 更新知识源文档计数
        source = await self.repository.find_source_by_id(document.source_id)
        if source is not None:
            source.decrement_document_count(operator)
            await self.repository.save_source(source)

        logger.info("文档删除成功: id=%s", document_id)

        return True
