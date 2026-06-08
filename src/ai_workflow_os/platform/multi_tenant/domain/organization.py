"""
组织实体

定义组织的核心业务实体，包含租户归属、成员管理等功能。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class Organization(BaseEntity):
    """组织实体

    核心业务实体，描述一个组织的完整信息。

    Attributes:
        tenant_id: 所属租户标识
        name: 组织名称
        description: 组织描述
        owner_id: 组织拥有者标识
        member_ids: 成员标识列表
        settings: 组织级配置
    """

    tenant_id: Optional[str] = None
    name: str = ""
    description: str = ""
    owner_id: str = ""
    member_ids: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)

    def add_member(self, user_id: str, operator: Optional[str] = None) -> None:
        """添加成员

        Args:
            user_id: 用户标识
            operator: 操作者标识
        """
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)
            self.touch(operator)

    def remove_member(self, user_id: str, operator: Optional[str] = None) -> None:
        """移除成员

        Args:
            user_id: 用户标识
            operator: 操作者标识
        """
        if user_id in self.member_ids:
            self.member_ids.remove(user_id)
            self.touch(operator)

    def is_member(self, user_id: str) -> bool:
        """判断用户是否为组织成员

        Args:
            user_id: 用户标识

        Returns:
            是否为成员
        """
        return user_id in self.member_ids or user_id == self.owner_id
