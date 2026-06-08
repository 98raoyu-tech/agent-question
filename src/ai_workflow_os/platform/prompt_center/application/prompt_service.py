"""
Prompt服务

提供Prompt模板的CRUD等业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.prompt_template import PromptTemplate
from ..infrastructure.prompt_repository import PromptRepository

logger = logging.getLogger(__name__)


class PromptService:
    """Prompt中心业务服务

    提供Prompt模板的完整生命周期管理。

    Attributes:
        repository: Prompt仓储实例
    """

    def __init__(self, repository: PromptRepository) -> None:
        """初始化Prompt服务

        Args:
            repository: Prompt仓储实例
        """
        self.repository = repository

    async def create_template(
        self,
        template: PromptTemplate,
        operator: Optional[str] = None,
    ) -> PromptTemplate:
        """创建Prompt模板

        Args:
            template: 模板实体
            operator: 操作者标识

        Returns:
            创建后的模板实体

        Raises:
            ValidationException: 名称为空
        """
        if not template.name or not template.name.strip():
            raise ValidationException(message="Prompt模板名称不能为空")

        template.created_by = operator
        template.updated_by = operator

        saved_template = await self.repository.save(template)
        logger.info("Prompt模板创建成功: id=%s, name=%s", saved_template.id, saved_template.name)

        return saved_template

    async def get_template(self, template_id: str) -> PromptTemplate:
        """获取Prompt模板详情

        Args:
            template_id: 模板标识

        Returns:
            模板实体

        Raises:
            ResourceNotFoundException: 模板不存在
        """
        template = await self.repository.find_by_id(template_id)
        if template is None:
            raise ResourceNotFoundException(resource_type="Prompt模板", resource_id=template_id)
        return template

    async def list_templates(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[PromptTemplate]:
        """分页查询模板列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all(pagination, tenant_id)

    async def update_template(
        self,
        template_id: str,
        template: PromptTemplate,
        operator: Optional[str] = None,
    ) -> PromptTemplate:
        """更新Prompt模板

        Args:
            template_id: 模板标识
            template: 更新后的模板数据
            operator: 操作者标识

        Returns:
            更新后的模板实体

        Raises:
            ResourceNotFoundException: 模板不存在
        """
        existing = await self.repository.find_by_id(template_id)
        if existing is None:
            raise ResourceNotFoundException(resource_type="Prompt模板", resource_id=template_id)

        existing.name = template.name
        existing.description = template.description
        existing.content = template.content
        existing.category = template.category
        existing.variables = template.variables
        existing.model_compatibility = template.model_compatibility
        existing.tags = template.tags
        existing.metadata = template.metadata
        existing.touch(operator)

        saved_template = await self.repository.save(existing)
        logger.info("Prompt模板更新成功: id=%s", template_id)

        return saved_template

    async def delete_template(self, template_id: str, operator: Optional[str] = None) -> bool:
        """删除Prompt模板（软删除）

        Args:
            template_id: 模板标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 模板不存在
        """
        template = await self.repository.find_by_id(template_id)
        if template is None:
            raise ResourceNotFoundException(resource_type="Prompt模板", resource_id=template_id)

        template.mark_deleted(operator)
        await self.repository.save(template)
        logger.info("Prompt模板删除成功: id=%s", template_id)

        return True
