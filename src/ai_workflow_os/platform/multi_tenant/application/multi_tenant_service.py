"""
多租户服务

提供租户、组织、项目、环境和RBAC的完整业务逻辑管理。
"""

import logging
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    TenantAccessException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import OrganizationRole, TenantStatus
from ..domain.environment import Environment
from ..domain.organization import Organization
from ..domain.project import Project
from ..domain.rbac import RoleAssignment
from ..domain.tenant import Tenant
from ..infrastructure.multi_tenant_repository import MultiTenantRepository

logger = logging.getLogger(__name__)

# 角色层级权重，数值越大权限越高
_ROLE_HIERARCHY: dict[OrganizationRole, int] = {
    OrganizationRole.VIEWER: 0,
    OrganizationRole.MEMBER: 1,
    OrganizationRole.ADMIN: 2,
    OrganizationRole.OWNER: 3,
}


class MultiTenantService:
    """多租户业务服务

    提供租户、组织、项目、环境和RBAC的完整生命周期管理。

    Attributes:
        repository: 多租户仓储实例
    """

    def __init__(self, repository: MultiTenantRepository) -> None:
        """初始化多租户服务

        Args:
            repository: 多租户仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 租户管理
    # =========================================================================

    async def create_tenant(
        self,
        tenant: Tenant,
        operator: Optional[str] = None,
    ) -> Tenant:
        """创建租户

        Args:
            tenant: 租户实体
            operator: 操作者标识

        Returns:
            创建后的租户实体

        Raises:
            ValidationException: 租户名称或标识为空
        """
        if not tenant.name or not tenant.name.strip():
            raise ValidationException(message="租户名称不能为空")

        if not tenant.slug or not tenant.slug.strip():
            raise ValidationException(message="租户标识(slug)不能为空")

        tenant.created_by = operator
        tenant.updated_by = operator

        saved_tenant = await self.repository.save_tenant(tenant)
        logger.info("租户创建成功: id=%s, name=%s", saved_tenant.id, saved_tenant.name)

        return saved_tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        """获取租户详情

        Args:
            tenant_id: 租户标识

        Returns:
            租户实体

        Raises:
            ResourceNotFoundException: 租户不存在
        """
        tenant = await self.repository.find_tenant_by_id(tenant_id)
        if tenant is None:
            raise ResourceNotFoundException(resource_type="租户", resource_id=tenant_id)
        return tenant

    async def list_tenants(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[Tenant]:
        """分页查询租户列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_tenants(pagination, filters)

    async def update_tenant(
        self,
        tenant_id: str,
        tenant: Tenant,
        operator: Optional[str] = None,
    ) -> Tenant:
        """更新租户

        Args:
            tenant_id: 租户标识
            tenant: 更新后的租户实体
            operator: 操作者标识

        Returns:
            更新后的租户实体

        Raises:
            ResourceNotFoundException: 租户不存在
        """
        existing_tenant = await self.get_tenant(tenant_id)

        existing_tenant.name = tenant.name
        existing_tenant.plan = tenant.plan
        existing_tenant.settings = tenant.settings
        existing_tenant.max_users = tenant.max_users
        existing_tenant.max_agents = tenant.max_agents
        existing_tenant.max_projects = tenant.max_projects
        existing_tenant.metadata = tenant.metadata
        existing_tenant.touch(operator)

        saved_tenant = await self.repository.save_tenant(existing_tenant)
        logger.info("租户更新成功: id=%s", tenant_id)

        return saved_tenant

    # =========================================================================
    # 组织管理
    # =========================================================================

    async def create_organization(
        self,
        organization: Organization,
        operator: Optional[str] = None,
    ) -> Organization:
        """创建组织

        Args:
            organization: 组织实体
            operator: 操作者标识

        Returns:
            创建后的组织实体

        Raises:
            ValidationException: 组织名称为空
            ResourceNotFoundException: 所属租户不存在
        """
        if not organization.name or not organization.name.strip():
            raise ValidationException(message="组织名称不能为空")

        # 校验所属租户存在且活跃
        if organization.tenant_id:
            tenant = await self.get_tenant(organization.tenant_id)
            if not tenant.is_active():
                raise BusinessRuleViolationException(
                    rule="ORG_TENANT_ACTIVE",
                    message="所属租户未激活，无法创建组织",
                )

        organization.created_by = operator
        organization.updated_by = operator

        # 创建者自动成为成员
        if operator and operator not in organization.member_ids:
            organization.member_ids.append(operator)

        saved_org = await self.repository.save_organization(organization)
        logger.info("组织创建成功: id=%s, name=%s", saved_org.id, saved_org.name)

        return saved_org

    async def get_organization(self, organization_id: str) -> Organization:
        """获取组织详情

        Args:
            organization_id: 组织标识

        Returns:
            组织实体

        Raises:
            ResourceNotFoundException: 组织不存在
        """
        org = await self.repository.find_organization_by_id(organization_id)
        if org is None:
            raise ResourceNotFoundException(resource_type="组织", resource_id=organization_id)
        return org

    async def list_organizations(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[Organization]:
        """分页查询组织列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_organizations(pagination, tenant_id, filters)

    # =========================================================================
    # 项目管理
    # =========================================================================

    async def create_project(
        self,
        project: Project,
        operator: Optional[str] = None,
    ) -> Project:
        """创建项目

        Args:
            project: 项目实体
            operator: 操作者标识

        Returns:
            创建后的项目实体

        Raises:
            ValidationException: 项目名称为空
            ResourceNotFoundException: 所属租户不存在
        """
        if not project.name or not project.name.strip():
            raise ValidationException(message="项目名称不能为空")

        # 校验所属租户存在且活跃
        if project.tenant_id:
            tenant = await self.get_tenant(project.tenant_id)
            if not tenant.is_active():
                raise BusinessRuleViolationException(
                    rule="PROJECT_TENANT_ACTIVE",
                    message="所属租户未激活，无法创建项目",
                )

        project.created_by = operator
        project.updated_by = operator

        # 创建者自动成为项目负责人
        if operator and operator not in project.member_roles:
            from ..domain.enums import ProjectRole
            project.member_roles[operator] = ProjectRole.LEAD

        saved_project = await self.repository.save_project(project)
        logger.info("项目创建成功: id=%s, name=%s", saved_project.id, saved_project.name)

        return saved_project

    async def get_project(self, project_id: str) -> Project:
        """获取项目详情

        Args:
            project_id: 项目标识

        Returns:
            项目实体

        Raises:
            ResourceNotFoundException: 项目不存在
        """
        project = await self.repository.find_project_by_id(project_id)
        if project is None:
            raise ResourceNotFoundException(resource_type="项目", resource_id=project_id)
        return project

    async def list_projects(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[Project]:
        """分页查询项目列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_projects(pagination, tenant_id, filters)

    # =========================================================================
    # 环境管理
    # =========================================================================

    async def create_environment(
        self,
        environment: Environment,
        operator: Optional[str] = None,
    ) -> Environment:
        """创建环境

        Args:
            environment: 环境实体
            operator: 操作者标识

        Returns:
            创建后的环境实体

        Raises:
            ValidationException: 环境名称为空
        """
        if not environment.name or not environment.name.strip():
            raise ValidationException(message="环境名称不能为空")

        # 校验所属租户存在且活跃
        if environment.tenant_id:
            tenant = await self.get_tenant(environment.tenant_id)
            if not tenant.is_active():
                raise BusinessRuleViolationException(
                    rule="ENV_TENANT_ACTIVE",
                    message="所属租户未激活，无法创建环境",
                )

        environment.created_by = operator
        environment.updated_by = operator

        saved_env = await self.repository.save_environment(environment)
        logger.info("环境创建成功: id=%s, name=%s", saved_env.id, saved_env.name)

        return saved_env

    async def list_environments(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[Environment]:
        """分页查询环境列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            project_id: 项目标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        merged_filters = dict(filters) if filters else {}
        if project_id:
            merged_filters["project_id"] = project_id
        return await self.repository.find_all_environments(pagination, tenant_id, merged_filters)

    # =========================================================================
    # RBAC管理
    # =========================================================================

    async def assign_role(
        self,
        role_assignment: RoleAssignment,
        operator: Optional[str] = None,
    ) -> RoleAssignment:
        """分配角色

        Args:
            role_assignment: 角色分配实体
            operator: 操作者标识

        Returns:
            创建后的角色分配实体

        Raises:
            ValidationException: 用户标识或角色为空
        """
        if not role_assignment.user_id:
            raise ValidationException(message="用户标识不能为空")

        if not role_assignment.scope_id:
            raise ValidationException(message="作用域标识不能为空")

        role_assignment.created_by = operator
        role_assignment.updated_by = operator
        role_assignment.granted_by = operator or ""

        saved_assignment = await self.repository.save_role_assignment(role_assignment)
        logger.info(
            "角色分配成功: user=%s, role=%s, scope=%s/%s",
            saved_assignment.user_id,
            saved_assignment.role.value,
            saved_assignment.scope_type,
            saved_assignment.scope_id,
        )

        return saved_assignment

    async def revoke_role(
        self,
        assignment_id: str,
        operator: Optional[str] = None,
    ) -> RoleAssignment:
        """撤销角色

        Args:
            assignment_id: 角色分配标识
            operator: 操作者标识

        Returns:
            撤销后的角色分配实体

        Raises:
            ResourceNotFoundException: 角色分配不存在
        """
        assignment = await self.repository.find_role_assignment_by_id(assignment_id)
        if assignment is None:
            raise ResourceNotFoundException(resource_type="角色分配", resource_id=assignment_id)

        assignment.revoke(operator)
        saved_assignment = await self.repository.save_role_assignment(assignment)
        logger.info("角色撤销成功: id=%s, user=%s", assignment_id, assignment.user_id)

        return saved_assignment

    async def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> list[RoleAssignment]:
        """获取用户的所有角色

        Args:
            user_id: 用户标识
            tenant_id: 租户标识

        Returns:
            角色分配列表（已过滤过期的）
        """
        assignments = await self.repository.find_roles_by_user(user_id, tenant_id)
        return [a for a in assignments if not a.is_expired()]

    async def check_permission(
        self,
        user_id: str,
        tenant_id: str,
        required_role: OrganizationRole,
    ) -> bool:
        """检查用户权限

        判断用户在指定租户下是否拥有不低于required_role的角色。

        Args:
            user_id: 用户标识
            tenant_id: 租户标识
            required_role: 所需的最低角色

        Returns:
            是否拥有权限
        """
        user_roles = await self.get_user_roles(user_id, tenant_id)

        required_level = _ROLE_HIERARCHY.get(required_role, 0)

        for assignment in user_roles:
            # 租户级别角色
            if assignment.scope_type == "tenant" and assignment.scope_id == tenant_id:
                user_level = _ROLE_HIERARCHY.get(assignment.role, 0)
                if user_level >= required_level:
                    return True
            # 组织或项目级别角色
            if assignment.scope_type in ("organization", "project"):
                user_level = _ROLE_HIERARCHY.get(assignment.role, 0)
                if user_level >= required_level:
                    return True

        return False
