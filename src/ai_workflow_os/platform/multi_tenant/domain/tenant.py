"""
租户实体

定义租户的核心业务实体，包含名称、标识、状态、套餐、配额和设置等。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import TenantStatus


@dataclass
class Tenant(BaseEntity):
    """租户实体

    核心业务实体，描述一个租户的完整信息。

    Attributes:
        name: 租户名称
        slug: 租户唯一标识符（URL友好）
        status: 租户状态
        plan: 套餐类型（free/pro/enterprise）
        settings: 租户级配置
        max_users: 最大用户数
        max_agents: 最大Agent数
        max_projects: 最大项目数
        metadata: 扩展元数据
    """

    name: str = ""
    slug: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    plan: str = "free"
    settings: dict[str, Any] = field(default_factory=dict)
    max_users: int = 10
    max_agents: int = 5
    max_projects: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活租户

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 租户已停用不可激活
        """
        if self.status == TenantStatus.DEACTIVATED:
            raise BusinessRuleViolationException(
                rule="TENANT_ACTIVATE_STATUS",
                message="已停用的租户不可激活，请重新创建",
            )
        self.status = TenantStatus.ACTIVE
        self.touch(operator)

    def suspend(self, operator: Optional[str] = None) -> None:
        """挂起租户

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 已停用的租户不可挂起
        """
        if self.status == TenantStatus.DEACTIVATED:
            raise BusinessRuleViolationException(
                rule="TENANT_SUSPEND_STATUS",
                message="已停用的租户不可挂起",
            )
        self.status = TenantStatus.SUSPENDED
        self.touch(operator)

    def deactivate(self, operator: Optional[str] = None) -> None:
        """停用租户

        Args:
            operator: 操作者标识
        """
        self.status = TenantStatus.DEACTIVATED
        self.touch(operator)

    def is_active(self) -> bool:
        """判断租户是否处于活跃状态

        Returns:
            是否为活跃状态
        """
        return self.status == TenantStatus.ACTIVE
