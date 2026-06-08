"""
多智能体组织业务服务

提供Agent注册、发现、通信、委托、团队管理和任务管理等核心业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_communication import AgentMessage
from ..domain.agent_delegation import AgentDelegation
from ..domain.agent_registry import AgentRegistryEntry
from ..domain.agent_task import AgentTask
from ..domain.agent_team import AgentTeam
from ..domain.enums import (
    AgentOrgStatus,
    AgentRole,
    TaskStatus,
    TeamStatus,
)
from ..infrastructure.multi_agent_org_repository import MultiAgentOrgRepository

logger = logging.getLogger(__name__)


class MultiAgentOrgService:
    """多智能体组织业务服务

    提供多智能体协作的完整业务逻辑，包括Agent注册/发现、消息通信、
    任务委托、团队管理和任务管理。

    Attributes:
        repository: 多智能体组织仓储实例
    """

    def __init__(self, repository: MultiAgentOrgRepository) -> None:
        """初始化多智能体组织服务

        Args:
            repository: 多智能体组织仓储实例
        """
        self.repository = repository

    # =========================================================================
    # Agent注册管理
    # =========================================================================

    async def register_agent(
        self,
        entry: AgentRegistryEntry,
        operator: Optional[str] = None,
    ) -> AgentRegistryEntry:
        """注册Agent

        Args:
            entry: Agent注册条目实体
            operator: 操作者标识

        Returns:
            注册后的Agent注册条目

        Raises:
            ValidationException: Agent标识为空
            BusinessRuleViolationException: Agent标识已存在
        """
        if not entry.agent_id:
            raise ValidationException(message="Agent标识不能为空")

        existing = await self.repository.find_agent_by_agent_id(entry.agent_id)
        if existing is not None:
            raise BusinessRuleViolationException(
                rule="AGENT_ALREADY_REGISTERED",
                message=f"Agent [{entry.agent_id}] 已注册",
            )

        entry.register(operator)
        return await self.repository.save_agent(entry)

    async def deregister_agent(
        self,
        agent_id: str,
        operator: Optional[str] = None,
    ) -> AgentRegistryEntry:
        """注销Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Returns:
            注销后的Agent注册条目

        Raises:
            ResourceNotFoundException: Agent未找到
        """
        entry = await self._get_agent_or_raise(agent_id)
        entry.deregister(operator)
        return await self.repository.save_agent(entry)

    async def discover_agents(
        self,
        capability: Optional[str] = None,
        role: Optional[AgentRole] = None,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentRegistryEntry]:
        """发现Agent

        根据能力和角色条件筛选可用的Agent。

        Args:
            capability: 能力过滤
            role: 角色过滤
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_agents(
            capability=capability,
            role=role,
            status=AgentOrgStatus.IDLE,
            pagination=pagination,
        )

    async def list_agents(
        self,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentRegistryEntry]:
        """列出所有Agent

        Args:
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_agents(pagination=pagination)

    # =========================================================================
    # 消息通信
    # =========================================================================

    async def send_message(
        self,
        message: AgentMessage,
        operator: Optional[str] = None,
    ) -> AgentMessage:
        """发送消息

        Args:
            message: 消息实体
            operator: 操作者标识

        Returns:
            发送后的消息实体

        Raises:
            ValidationException: 发送方或接收方为空
        """
        if not message.sender_agent_id:
            raise ValidationException(message="发送方Agent标识不能为空")
        if not message.receiver_agent_id:
            raise ValidationException(message="接收方Agent标识不能为空")

        message.touch(operator)
        return await self.repository.save_message(message)

    async def get_messages(
        self,
        agent_id: str,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentMessage]:
        """获取Agent消息列表

        Args:
            agent_id: Agent标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_messages_by_agent(agent_id, pagination)

    # =========================================================================
    # 任务委托
    # =========================================================================

    async def delegate_task(
        self,
        delegation: AgentDelegation,
        operator: Optional[str] = None,
    ) -> AgentDelegation:
        """委托任务

        Args:
            delegation: 委托实体
            operator: 操作者标识

        Returns:
            创建后的委托实体

        Raises:
            ValidationException: 委托方或被委托方为空
            ResourceNotFoundException: 被委托Agent未找到
            BusinessRuleViolationException: 被委托Agent不可用
        """
        if not delegation.delegator_agent_id:
            raise ValidationException(message="委托方Agent标识不能为空")
        if not delegation.delegate_agent_id:
            raise ValidationException(message="被委托方Agent标识不能为空")

        delegate = await self.repository.find_agent_by_agent_id(delegation.delegate_agent_id)
        if delegate is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=delegation.delegate_agent_id)
        if not delegate.can_accept_task():
            raise BusinessRuleViolationException(
                rule="AGENT_NOT_AVAILABLE",
                message=f"Agent [{delegation.delegate_agent_id}] 当前不可接受新任务",
            )

        delegate.increment_task_count(operator)
        await self.repository.save_agent(delegate)
        delegation.touch(operator)
        return await self.repository.save_delegation(delegation)

    async def accept_delegation(
        self,
        delegation_id: str,
        operator: Optional[str] = None,
    ) -> AgentDelegation:
        """接受委托

        Args:
            delegation_id: 委托标识
            operator: 操作者标识

        Returns:
            更新后的委托实体

        Raises:
            ResourceNotFoundException: 委托未找到
        """
        delegation = await self._get_delegation_or_raise(delegation_id)
        delegation.accept(operator)
        return await self.repository.save_delegation(delegation)

    async def complete_delegation(
        self,
        delegation_id: str,
        result: dict,
        operator: Optional[str] = None,
    ) -> AgentDelegation:
        """完成委托

        Args:
            delegation_id: 委托标识
            result: 执行结果
            operator: 操作者标识

        Returns:
            更新后的委托实体

        Raises:
            ResourceNotFoundException: 委托未找到
        """
        delegation = await self._get_delegation_or_raise(delegation_id)

        # 释放被委托Agent的任务计数
        delegate = await self.repository.find_agent_by_agent_id(delegation.delegate_agent_id)
        if delegate is not None:
            delegate.decrement_task_count(operator)
            await self.repository.save_agent(delegate)

        delegation.complete(result, operator)
        return await self.repository.save_delegation(delegation)

    # =========================================================================
    # 团队管理
    # =========================================================================

    async def create_team(
        self,
        team: AgentTeam,
        operator: Optional[str] = None,
    ) -> AgentTeam:
        """创建团队

        Args:
            team: 团队实体
            operator: 操作者标识

        Returns:
            创建后的团队实体

        Raises:
            ValidationException: 团队名称为空
        """
        if not team.name:
            raise ValidationException(message="团队名称不能为空")

        team.touch(operator)
        return await self.repository.save_team(team)

    async def add_team_member(
        self,
        team_id: str,
        agent_id: str,
        role: AgentRole,
        operator: Optional[str] = None,
    ) -> AgentTeam:
        """添加团队成员

        Args:
            team_id: 团队标识
            agent_id: Agent标识
            role: Agent角色
            operator: 操作者标识

        Returns:
            更新后的团队实体

        Raises:
            ResourceNotFoundException: 团队或Agent未找到
        """
        team = await self._get_team_or_raise(team_id)

        agent = await self.repository.find_agent_by_agent_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)

        team.add_member(agent_id, role, operator)
        return await self.repository.save_team(team)

    async def disband_team(
        self,
        team_id: str,
        operator: Optional[str] = None,
    ) -> AgentTeam:
        """解散团队

        Args:
            team_id: 团队标识
            operator: 操作者标识

        Returns:
            更新后的团队实体

        Raises:
            ResourceNotFoundException: 团队未找到
        """
        team = await self._get_team_or_raise(team_id)
        team.disband(operator)
        return await self.repository.save_team(team)

    async def get_team_status(self, team_id: str) -> AgentTeam:
        """获取团队状态

        Args:
            team_id: 团队标识

        Returns:
            团队实体

        Raises:
            ResourceNotFoundException: 团队未找到
        """
        return await self._get_team_or_raise(team_id)

    async def list_teams(
        self,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentTeam]:
        """列出所有团队

        Args:
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_teams(pagination=pagination)

    # =========================================================================
    # 任务管理
    # =========================================================================

    async def create_task(
        self,
        task: AgentTask,
        operator: Optional[str] = None,
    ) -> AgentTask:
        """创建任务

        Args:
            task: 任务实体
            operator: 操作者标识

        Returns:
            创建后的任务实体

        Raises:
            ValidationException: 任务标题为空
        """
        if not task.title:
            raise ValidationException(message="任务标题不能为空")

        task.touch(operator)
        return await self.repository.save_task(task)

    async def assign_task(
        self,
        task_id: str,
        agent_id: str,
        operator: Optional[str] = None,
    ) -> AgentTask:
        """分配任务

        Args:
            task_id: 任务标识
            agent_id: Agent标识
            operator: 操作者标识

        Returns:
            更新后的任务实体

        Raises:
            ResourceNotFoundException: 任务或Agent未找到
            BusinessRuleViolationException: Agent不可用
        """
        task = await self._get_task_or_raise(task_id)

        agent = await self.repository.find_agent_by_agent_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(resource_type="Agent", resource_id=agent_id)
        if not agent.can_accept_task():
            raise BusinessRuleViolationException(
                rule="AGENT_NOT_AVAILABLE",
                message=f"Agent [{agent_id}] 当前不可接受新任务",
            )

        task.assign(agent_id, operator)
        agent.increment_task_count(operator)
        await self.repository.save_agent(agent)
        return await self.repository.save_task(task)

    async def complete_task(
        self,
        task_id: str,
        result: dict,
        operator: Optional[str] = None,
    ) -> AgentTask:
        """完成任务

        Args:
            task_id: 任务标识
            result: 执行结果
            operator: 操作者标识

        Returns:
            更新后的任务实体

        Raises:
            ResourceNotFoundException: 任务未找到
        """
        task = await self._get_task_or_raise(task_id)
        task.complete(result, operator)

        # 释放Agent的任务计数
        if task.assigned_agent_id:
            agent = await self.repository.find_agent_by_agent_id(task.assigned_agent_id)
            if agent is not None:
                agent.decrement_task_count(operator)
                await self.repository.save_agent(agent)

        return await self.repository.save_task(task)

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _get_agent_or_raise(self, agent_id: str) -> AgentRegistryEntry:
        """获取Agent注册条目，不存在则抛出异常

        Args:
            agent_id: Agent标识

        Returns:
            Agent注册条目实体

        Raises:
            ResourceNotFoundException: Agent未找到
        """
        entry = await self.repository.find_agent_by_agent_id(agent_id)
        if entry is None:
            raise ResourceNotFoundException(resource_type="Agent注册条目", resource_id=agent_id)
        return entry

    async def _get_delegation_or_raise(self, delegation_id: str) -> AgentDelegation:
        """获取委托实体，不存在则抛出异常

        Args:
            delegation_id: 委托标识

        Returns:
            委托实体

        Raises:
            ResourceNotFoundException: 委托未找到
        """
        delegation = await self.repository.find_delegation_by_id(delegation_id)
        if delegation is None:
            raise ResourceNotFoundException(resource_type="委托", resource_id=delegation_id)
        return delegation

    async def _get_team_or_raise(self, team_id: str) -> AgentTeam:
        """获取团队实体，不存在则抛出异常

        Args:
            team_id: 团队标识

        Returns:
            团队实体

        Raises:
            ResourceNotFoundException: 团队未找到
        """
        team = await self.repository.find_team_by_id(team_id)
        if team is None:
            raise ResourceNotFoundException(resource_type="团队", resource_id=team_id)
        return team

    async def _get_task_or_raise(self, task_id: str) -> AgentTask:
        """获取任务实体，不存在则抛出异常

        Args:
            task_id: 任务标识

        Returns:
            任务实体

        Raises:
            ResourceNotFoundException: 任务未找到
        """
        task = await self.repository.find_task_by_id(task_id)
        if task is None:
            raise ResourceNotFoundException(resource_type="任务", resource_id=task_id)
        return task
