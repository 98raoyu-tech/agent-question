"""
Agent团队实体

定义多智能体团队的核心领域实体，管理团队的组建、成员管理、领导指派和能力维护。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import AgentRole, TeamStatus


@dataclass
class AgentTeam(BaseEntity):
    """Agent团队实体

    表示一个由多个Agent组成的协作团队，支持动态成员管理、领导指派和能力聚合。

    Attributes:
        name: 团队名称
        description: 团队描述
        team_status: 团队状态
        leader_agent_id: 团队领导Agent标识
        member_ids: 成员Agent标识列表
        member_roles: 成员角色映射（agent_id -> AgentRole）
        capabilities: 团队聚合能力列表
        max_members: 最大成员数
        active_delegation_ids: 活跃委托标识列表
    """

    name: str = ""
    description: str = ""
    team_status: TeamStatus = TeamStatus.FORMING
    leader_agent_id: str = ""
    member_ids: list[str] = field(default_factory=list)
    member_roles: dict[str, AgentRole] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    max_members: int = 20
    active_delegation_ids: list[str] = field(default_factory=list)

    def add_member(self, agent_id: str, role: AgentRole, operator: Optional[str] = None) -> None:
        """添加团队成员

        Args:
            agent_id: Agent标识
            role: Agent角色
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 团队已解散、成员已满或成员已存在
        """
        if self.team_status == TeamStatus.DISBANDED:
            raise BusinessRuleViolationException(
                rule="TEAM_ALREADY_DISBANDED",
                message=f"团队 [{self.id}] 已解散，无法添加成员",
            )
        if agent_id in self.member_ids:
            raise BusinessRuleViolationException(
                rule="MEMBER_ALREADY_EXISTS",
                message=f"Agent [{agent_id}] 已是团队 [{self.id}] 的成员",
            )
        if len(self.member_ids) >= self.max_members:
            raise BusinessRuleViolationException(
                rule="TEAM_MEMBER_LIMIT_REACHED",
                message=f"团队 [{self.id}] 已达最大成员数 {self.max_members}",
            )
        self.member_ids.append(agent_id)
        self.member_roles[agent_id] = role
        self.touch(operator)

    def remove_member(self, agent_id: str, operator: Optional[str] = None) -> None:
        """移除团队成员

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 成员不存在或是团队领导
        """
        if agent_id not in self.member_ids:
            raise BusinessRuleViolationException(
                rule="MEMBER_NOT_FOUND",
                message=f"Agent [{agent_id}] 不是团队 [{self.id}] 的成员",
            )
        if agent_id == self.leader_agent_id:
            raise BusinessRuleViolationException(
                rule="CANNOT_REMOVE_LEADER",
                message=f"Agent [{agent_id}] 是团队领导，请先更换领导后再移除",
            )
        self.member_ids.remove(agent_id)
        self.member_roles.pop(agent_id, None)
        self.touch(operator)

    def assign_leader(self, agent_id: str, operator: Optional[str] = None) -> None:
        """指派团队领导

        Args:
            agent_id: Agent标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: Agent不是团队成员
        """
        if agent_id not in self.member_ids:
            raise BusinessRuleViolationException(
                rule="LEADER_MUST_BE_MEMBER",
                message=f"Agent [{agent_id}] 不是团队 [{self.id}] 的成员，无法指派为领导",
            )
        self.leader_agent_id = agent_id
        self.touch(operator)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活团队

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 团队状态不允许激活或成员不足
        """
        if self.team_status != TeamStatus.FORMING:
            raise BusinessRuleViolationException(
                rule="TEAM_STATUS_TRANSITION",
                message=f"团队 [{self.id}] 当前状态为 {self.team_status.value}，无法激活",
            )
        if len(self.member_ids) == 0:
            raise BusinessRuleViolationException(
                rule="TEAM_NO_MEMBERS",
                message=f"团队 [{self.id}] 没有成员，无法激活",
            )
        if not self.leader_agent_id:
            raise BusinessRuleViolationException(
                rule="TEAM_NO_LEADER",
                message=f"团队 [{self.id}] 未指派领导，无法激活",
            )
        self.team_status = TeamStatus.ACTIVE
        self.touch(operator)

    def disband(self, operator: Optional[str] = None) -> None:
        """解散团队

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 团队已有解散后的状态
        """
        if self.team_status == TeamStatus.DISBANDED:
            raise BusinessRuleViolationException(
                rule="TEAM_ALREADY_DISBANDED",
                message=f"团队 [{self.id}] 已解散",
            )
        self.team_status = TeamStatus.DISBANDED
        self.member_ids.clear()
        self.member_roles.clear()
        self.active_delegation_ids.clear()
        self.touch(operator)

    def get_members_by_role(self, role: AgentRole) -> list[str]:
        """获取指定角色的成员列表

        Args:
            role: Agent角色

        Returns:
            具有该角色的Agent标识列表
        """
        return [agent_id for agent_id, member_role in self.member_roles.items() if member_role == role]

    def has_capability(self, capability: str) -> bool:
        """判断团队是否具有指定能力

        Args:
            capability: 能力标识

        Returns:
            团队具有该能力返回True
        """
        return capability in self.capabilities
