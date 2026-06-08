"""
RBAC角色分配实体

定义角色分配的核心业务实体，包含租户归属、用户角色、作用域和过期管理等功能。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ...common.base_entity import BaseEntity
from .enums import OrganizationRole


@dataclass
class RoleAssignment(BaseEntity):
    """角色分配实体

    核心业务实体，描述一个角色分配的完整信息。

    Attributes:
        tenant_id: 所属租户标识
        user_id: 用户标识
        role: 组织角色
        scope_type: 作用域类型（tenant/organization/project）
        scope_id: 作用域标识
        granted_by: 授权者标识
        granted_at: 授权时间
        expires_at: 过期时间
    """

    tenant_id: Optional[str] = None
    user_id: str = ""
    role: OrganizationRole = OrganizationRole.MEMBER
    scope_type: str = "tenant"
    scope_id: str = ""
    granted_by: str = ""
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """判断角色分配是否已过期

        Returns:
            是否已过期
        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def revoke(self, operator: Optional[str] = None) -> None:
        """撤销角色分配

        通过设置过期时间为当前时间来撤销角色。

        Args:
            operator: 操作者标识
        """
        self.expires_at = datetime.now(timezone.utc)
        self.touch(operator)
