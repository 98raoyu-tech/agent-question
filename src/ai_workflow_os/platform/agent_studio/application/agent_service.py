"""
Agent服务

提供Agent的CRUD、版本管理、发布和回滚等业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_definition import AgentDefinition
from ..domain.agent_release import AgentRelease
from ..domain.agent_version import AgentVersion
from ..domain.enums import AgentStatus
from ..infrastructure.agent_repository import AgentRepository

logger = logging.getLogger(__name__)


class AgentService:
    """Agent业务服务

    提供Agent的完整生命周期管理，包括创建、更新、版本管理、发布和回滚。

    Attributes:
        repository: Agent仓储实例
    """

    def __init__(self, repository: AgentRepository) -> None:
        """初始化Agent服务

        Args:
            repository: Agent仓储实例
        """
        self.repository = repository

    async def create_agent(
        self,
        agent: AgentDefinition,
        operator: Optional[str] = None,
    ) -> AgentDefinition:
        """创建Agent

        Args:
            agent: Agent定义实体
            operator: 操作者标识

        Returns:
            创建后的Agent实体

        Raises:
            ValidationException: Agent名称为空
        """
        # 校验Agent名称
        if not agent.name or not agent.name.strip():
            raise ValidationException(message="Agent名称不能为空")

        # 设置创建者
        agent.created_by = operator
        agent.updated_by = operator

        # 保存Agent
        saved_agent = await self.repository.save(agent)
        logger.info("Agent创建成功: id=%s, name=%s", saved_agent.id, saved_agent.name)

        # 创建初始版本
        await self._create_version(saved_agent, "初始版本", operator)

        return saved_agent

    async def update_agent(
        self,
        agent_id: str,
        agent: AgentDefinition,
        operator: Optional[str] = None,
    ) -> AgentDefinition:
        """更新Agent

        Args:
            agent_id: Agent标识
            agent: 更新后的Agent定义
            operator: 操作者标识

        Returns:
            更新后的Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: Agent状态不允许更新
        """
        # 查找现有Agent
        existing_agent = await self.repository.find_by_id(agent_id)
        if existing_agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)

        # 只有草稿状态的Agent才能更新
        if existing_agent.status != AgentStatus.DRAFT:
            raise BusinessRuleViolationException(
                rule="AGENT_UPDATE_STATUS",
                message=f"Agent当前状态为{existing_agent.status.value}，只有草稿状态的Agent才能更新",
            )

        # 更新字段
        existing_agent.name = agent.name
        existing_agent.description = agent.description
        existing_agent.agent_type = agent.agent_type
        existing_agent.system_prompt = agent.system_prompt
        existing_agent.model_config = agent.model_config
        existing_agent.tools = agent.tools
        existing_agent.knowledge_sources = agent.knowledge_sources
        existing_agent.tags = agent.tags
        existing_agent.metadata = agent.metadata
        existing_agent.touch(operator)

        # 保存更新
        saved_agent = await self.repository.save(existing_agent)
        logger.info("Agent更新成功: id=%s", agent_id)

        return saved_agent

    async def get_agent(self, agent_id: str) -> AgentDefinition:
        """获取Agent详情

        Args:
            agent_id: Agent标识

        Returns:
            Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        agent = await self.repository.find_by_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)
        return agent

    async def list_agents(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[AgentDefinition]:
        """分页查询Agent列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all(pagination, tenant_id)

    async def delete_agent(self, agent_id: str, operator: Optional[str] = None) -> bool:
        """删除Agent（软删除）

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: 已发布的Agent不能删除
        """
        agent = await self.repository.find_by_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)

        # 已发布的Agent不能删除
        if agent.status == AgentStatus.PUBLISHED:
            raise BusinessRuleViolationException(
                rule="AGENT_DELETE_STATUS",
                message="已发布的Agent不能删除，请先归档",
            )

        agent.mark_deleted(operator)
        await self.repository.save(agent)
        logger.info("Agent删除成功: id=%s", agent_id)

        return True

    async def publish_agent(
        self,
        agent_id: str,
        release_name: str = "",
        release_notes: str = "",
        operator: Optional[str] = None,
    ) -> AgentRelease:
        """发布Agent

        Args:
            agent_id: Agent标识
            release_name: 发布名称
            release_notes: 发布说明
            operator: 操作者标识

        Returns:
            发布记录

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: Agent状态不允许发布
        """
        agent = await self.repository.find_by_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)

        # 只有草稿状态的Agent才能发布
        if agent.status != AgentStatus.DRAFT:
            raise BusinessRuleViolationException(
                rule="AGENT_PUBLISH_STATUS",
                message=f"Agent当前状态为{agent.status.value}，只有草稿状态的Agent才能发布",
            )

        # 更新Agent状态
        agent.publish(operator)
        await self.repository.save(agent)

        # 创建发布记录
        release = AgentRelease(
            agent_id=agent_id,
            release_name=release_name or f"Release-{agent.name}",
            release_notes=release_notes,
        )
        release.start_release(operator)
        release.complete_release(operator)

        logger.info("Agent发布成功: id=%s, release=%s", agent_id, release.release_name)

        return release

    async def archive_agent(self, agent_id: str, operator: Optional[str] = None) -> AgentDefinition:
        """归档Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Returns:
            归档后的Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        agent = await self.repository.find_by_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)

        agent.archive(operator)
        saved_agent = await self.repository.save(agent)
        logger.info("Agent归档成功: id=%s", agent_id)

        return saved_agent

    async def _create_version(
        self,
        agent: AgentDefinition,
        change_log: str = "",
        operator: Optional[str] = None,
    ) -> AgentVersion:
        """创建Agent版本快照

        Args:
            agent: Agent实体
            change_log: 变更日志
            operator: 操作者标识

        Returns:
            版本实体
        """
        import json
        from dataclasses import asdict

        # 创建快照
        snapshot = asdict(agent)

        version = AgentVersion(
            agent_id=agent.id,
            version_number=f"v{agent.version}",
            change_log=change_log,
            snapshot=snapshot,
            is_current=True,
            created_by=operator,
        )

        logger.info("Agent版本创建成功: agent_id=%s, version=%s", agent.id, version.version_number)

        return version
