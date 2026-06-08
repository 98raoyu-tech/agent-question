"""
多智能体组织仓储实现

提供Agent注册表、消息、委托、团队和任务的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_communication import AgentMessage
from ..domain.agent_delegation import AgentDelegation
from ..domain.agent_registry import AgentRegistryEntry
from ..domain.agent_task import AgentTask
from ..domain.agent_team import AgentTeam
from ..domain.enums import AgentOrgStatus, AgentRole, TeamStatus

logger = logging.getLogger(__name__)


class MultiAgentOrgRepository:
    """多智能体组织仓储实现

    基于内存字典的仓储实现，管理Agent注册表、消息、委托、团队和任务的持久化。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._agents: dict[str, AgentRegistryEntry] = {}
        self._messages: dict[str, AgentMessage] = {}
        self._delegations: dict[str, AgentDelegation] = {}
        self._teams: dict[str, AgentTeam] = {}
        self._tasks: dict[str, AgentTask] = {}

    # =========================================================================
    # Agent注册表操作
    # =========================================================================

    async def save_agent(self, entry: AgentRegistryEntry) -> AgentRegistryEntry:
        """保存Agent注册条目

        Args:
            entry: Agent注册条目实体

        Returns:
            保存后的实体
        """
        self._agents[entry.id] = entry
        return entry

    async def find_agent_by_id(self, entry_id: str) -> Optional[AgentRegistryEntry]:
        """根据ID查找Agent注册条目

        Args:
            entry_id: 注册条目标识

        Returns:
            注册条目实体，未找到返回None
        """
        entry = self._agents.get(entry_id)
        if entry is not None and entry.is_deleted:
            return None
        return entry

    async def find_agent_by_agent_id(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """根据Agent标识查找注册条目

        Args:
            agent_id: Agent标识

        Returns:
            注册条目实体，未找到返回None
        """
        for entry in self._agents.values():
            if entry.agent_id == agent_id and not entry.is_deleted:
                return entry
        return None

    async def find_agents(
        self,
        capability: Optional[str] = None,
        role: Optional[AgentRole] = None,
        status: Optional[AgentOrgStatus] = None,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentRegistryEntry]:
        """查询Agent注册列表

        Args:
            capability: 能力过滤
            role: 角色过滤
            status: 状态过滤
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        agents = [a for a in self._agents.values() if not a.is_deleted]

        if capability is not None:
            agents = [a for a in agents if capability in a.capabilities]

        if role is not None:
            agents = [a for a in agents if a.agent_role == role]

        if status is not None:
            agents = [a for a in agents if a.status == status]

        agents.sort(key=lambda a: a.created_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(agents)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = agents[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def delete_agent(self, entry_id: str) -> None:
        """删除Agent注册条目（标记为已删除）

        Args:
            entry_id: 注册条目标识
        """
        entry = self._agents.get(entry_id)
        if entry is not None:
            self._agents.pop(entry_id)

    # =========================================================================
    # 消息操作
    # =========================================================================

    async def save_message(self, message: AgentMessage) -> AgentMessage:
        """保存消息

        Args:
            message: 消息实体

        Returns:
            保存后的消息实体
        """
        self._messages[message.id] = message
        return message

    async def find_message_by_id(self, message_id: str) -> Optional[AgentMessage]:
        """根据ID查找消息

        Args:
            message_id: 消息标识

        Returns:
            消息实体，未找到返回None
        """
        message = self._messages.get(message_id)
        if message is not None and message.is_deleted:
            return None
        return message

    async def find_messages_by_agent(
        self,
        agent_id: str,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentMessage]:
        """查询Agent相关消息

        Args:
            agent_id: Agent标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        messages = [
            m for m in self._messages.values()
            if not m.is_deleted and (m.sender_agent_id == agent_id or m.receiver_agent_id == agent_id)
        ]
        messages.sort(key=lambda m: m.sent_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(messages)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = messages[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # =========================================================================
    # 委托操作
    # =========================================================================

    async def save_delegation(self, delegation: AgentDelegation) -> AgentDelegation:
        """保存委托

        Args:
            delegation: 委托实体

        Returns:
            保存后的委托实体
        """
        self._delegations[delegation.id] = delegation
        return delegation

    async def find_delegation_by_id(self, delegation_id: str) -> Optional[AgentDelegation]:
        """根据ID查找委托

        Args:
            delegation_id: 委托标识

        Returns:
            委托实体，未找到返回None
        """
        delegation = self._delegations.get(delegation_id)
        if delegation is not None and delegation.is_deleted:
            return None
        return delegation

    # =========================================================================
    # 团队操作
    # =========================================================================

    async def save_team(self, team: AgentTeam) -> AgentTeam:
        """保存团队

        Args:
            team: 团队实体

        Returns:
            保存后的团队实体
        """
        self._teams[team.id] = team
        return team

    async def find_team_by_id(self, team_id: str) -> Optional[AgentTeam]:
        """根据ID查找团队

        Args:
            team_id: 团队标识

        Returns:
            团队实体，未找到返回None
        """
        team = self._teams.get(team_id)
        if team is not None and team.is_deleted:
            return None
        return team

    async def find_teams(
        self,
        status: Optional[TeamStatus] = None,
        pagination: Optional[PaginatedRequest] = None,
    ) -> PaginatedResponse[AgentTeam]:
        """查询团队列表

        Args:
            status: 状态过滤
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        teams = [t for t in self._teams.values() if not t.is_deleted]

        if status is not None:
            teams = [t for t in teams if t.team_status == status]

        teams.sort(key=lambda t: t.created_at, reverse=True)

        if pagination is None:
            pagination = PaginatedRequest()

        total = len(teams)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = teams[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # =========================================================================
    # 任务操作
    # =========================================================================

    async def save_task(self, task: AgentTask) -> AgentTask:
        """保存任务

        Args:
            task: 任务实体

        Returns:
            保存后的任务实体
        """
        self._tasks[task.id] = task
        return task

    async def find_task_by_id(self, task_id: str) -> Optional[AgentTask]:
        """根据ID查找任务

        Args:
            task_id: 任务标识

        Returns:
            任务实体，未找到返回None
        """
        task = self._tasks.get(task_id)
        if task is not None and task.is_deleted:
            return None
        return task
