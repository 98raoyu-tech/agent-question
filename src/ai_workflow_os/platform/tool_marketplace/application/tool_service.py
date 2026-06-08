"""
工具服务

提供工具定义的CRUD等业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.tool_definition import ToolDefinition
from ..infrastructure.tool_repository import ToolRepository

logger = logging.getLogger(__name__)


class ToolService:
    """工具市场业务服务

    提供工具定义的完整生命周期管理。

    Attributes:
        repository: 工具仓储实例
    """

    def __init__(self, repository: ToolRepository) -> None:
        """初始化工具服务

        Args:
            repository: 工具仓储实例
        """
        self.repository = repository

    async def create_tool(
        self,
        tool: ToolDefinition,
        operator: Optional[str] = None,
    ) -> ToolDefinition:
        """创建工具定义

        Args:
            tool: 工具定义实体
            operator: 操作者标识

        Returns:
            创建后的工具实体

        Raises:
            ValidationException: 名称为空
        """
        if not tool.name or not tool.name.strip():
            raise ValidationException(message="工具名称不能为空")

        tool.created_by = operator
        tool.updated_by = operator

        saved_tool = await self.repository.save(tool)
        logger.info("工具创建成功: id=%s, name=%s", saved_tool.id, saved_tool.name)

        return saved_tool

    async def get_tool(self, tool_id: str) -> ToolDefinition:
        """获取工具详情

        Args:
            tool_id: 工具标识

        Returns:
            工具实体

        Raises:
            ResourceNotFoundException: 工具不存在
        """
        tool = await self.repository.find_by_id(tool_id)
        if tool is None:
            raise ResourceNotFoundException(resource_type="工具", resource_id=tool_id)
        return tool

    async def list_tools(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[ToolDefinition]:
        """分页查询工具列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all(pagination, tenant_id)

    async def update_tool(
        self,
        tool_id: str,
        tool: ToolDefinition,
        operator: Optional[str] = None,
    ) -> ToolDefinition:
        """更新工具定义

        Args:
            tool_id: 工具标识
            tool: 更新后的工具数据
            operator: 操作者标识

        Returns:
            更新后的工具实体

        Raises:
            ResourceNotFoundException: 工具不存在
        """
        existing = await self.repository.find_by_id(tool_id)
        if existing is None:
            raise ResourceNotFoundException(resource_type="工具", resource_id=tool_id)

        existing.name = tool.name
        existing.description = tool.description
        existing.tool_type = tool.tool_type
        existing.endpoint = tool.endpoint
        existing.parameters = tool.parameters
        existing.return_type = tool.return_type
        existing.authentication = tool.authentication
        existing.timeout = tool.timeout
        existing.retry_count = tool.retry_count
        existing.author = tool.author
        existing.tags = tool.tags
        existing.metadata = tool.metadata
        existing.touch(operator)

        saved_tool = await self.repository.save(existing)
        logger.info("工具更新成功: id=%s", tool_id)

        return saved_tool

    async def delete_tool(self, tool_id: str, operator: Optional[str] = None) -> bool:
        """删除工具定义（软删除）

        Args:
            tool_id: 工具标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 工具不存在
        """
        tool = await self.repository.find_by_id(tool_id)
        if tool is None:
            raise ResourceNotFoundException(resource_type="工具", resource_id=tool_id)

        tool.mark_deleted(operator)
        await self.repository.save(tool)
        logger.info("工具删除成功: id=%s", tool_id)

        return True
