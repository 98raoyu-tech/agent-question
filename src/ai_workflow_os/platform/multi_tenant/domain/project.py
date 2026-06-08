"""
项目实体

定义项目的核心业务实体，包含租户和组织归属、成员角色管理、Agent管理等功能。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import ProjectRole, ResourceEnvironment


@dataclass
class Project(BaseEntity):
    """项目实体

    核心业务实体，描述一个项目的完整信息。

    Attributes:
        tenant_id: 所属租户标识
        organization_id: 所属组织标识
        name: 项目名称
        description: 项目描述
        environment: 项目环境
        owner_id: 项目拥有者标识
        member_roles: 成员角色映射（user_id -> ProjectRole）
        settings: 项目级配置
        agent_ids: 关联的Agent标识列表
    """

    tenant_id: Optional[str] = None
    organization_id: str = ""
    name: str = ""
    description: str = ""
    environment: ResourceEnvironment = ResourceEnvironment.DEV
    owner_id: str = ""
    member_roles: dict[str, ProjectRole] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    agent_ids: list[str] = field(default_factory=list)

    def assign_member(
        self,
        user_id: str,
        role: ProjectRole,
        operator: Optional[str] = None,
    ) -> None:
        """分配成员角色

        Args:
            user_id: 用户标识
            role: 项目角色
            operator: 操作者标识
        """
        self.member_roles[user_id] = role
        self.touch(operator)

    def remove_member(self, user_id: str, operator: Optional[str] = None) -> None:
        """移除成员

        Args:
            user_id: 用户标识
            operator: 操作者标识
        """
        if user_id in self.member_roles:
            del self.member_roles[user_id]
            self.touch(operator)

    def add_agent(self, agent_id: str, operator: Optional[str] = None) -> None:
        """添加Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识
        """
        if agent_id not in self.agent_ids:
            self.agent_ids.append(agent_id)
            self.touch(operator)

    def remove_agent(self, agent_id: str, operator: Optional[str] = None) -> None:
        """移除Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识
        """
        if agent_id in self.agent_ids:
            self.agent_ids.remove(agent_id)
            self.touch(operator)

    def get_member_role(self, user_id: str) -> Optional[ProjectRole]:
        """获取成员角色

        Args:
            user_id: 用户标识

        Returns:
            项目角色，未找到返回None
        """
        return self.member_roles.get(user_id)
