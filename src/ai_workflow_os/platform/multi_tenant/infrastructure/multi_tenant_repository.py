"""
多租户仓储实现

提供租户、组织、项目、环境和角色分配的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.environment import Environment
from ..domain.organization import Organization
from ..domain.project import Project
from ..domain.rbac import RoleAssignment
from ..domain.tenant import Tenant

logger = logging.getLogger(__name__)


class MultiTenantRepository:
    """多租户仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._tenants: dict[str, Tenant] = {}
        self._organizations: dict[str, Organization] = {}
        self._projects: dict[str, Project] = {}
        self._environments: dict[str, Environment] = {}
        self._role_assignments: dict[str, RoleAssignment] = {}

    # =========================================================================
    # 租户仓储
    # =========================================================================

    async def find_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """根据ID查找租户

        Args:
            tenant_id: 租户标识

        Returns:
            租户实体，未找到返回None
        """
        tenant = self._tenants.get(tenant_id)
        if tenant is not None and tenant.is_deleted:
            return None
        return tenant

    async def find_all_tenants(
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
        tenants = [t for t in self._tenants.values() if not t.is_deleted]

        if filters:
            if "status" in filters:
                tenants = [t for t in tenants if t.status.value == filters["status"]]
            if "plan" in filters:
                tenants = [t for t in tenants if t.plan == filters["plan"]]
            if "search" in filters and filters["search"]:
                search_term = filters["search"].lower()
                tenants = [
                    t for t in tenants
                    if search_term in t.name.lower() or search_term in t.slug.lower()
                ]

        if pagination.sort_by and hasattr(Tenant, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            tenants.sort(key=lambda t: getattr(t, pagination.sort_by, ""), reverse=reverse)
        else:
            tenants.sort(key=lambda t: t.created_at, reverse=True)

        total = len(tenants)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = tenants[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_tenant(self, entity: Tenant) -> Tenant:
        """保存租户

        Args:
            entity: 租户实体

        Returns:
            保存后的租户实体
        """
        self._tenants[entity.id] = entity
        logger.debug("租户已保存: id=%s", entity.id)
        return entity

    # =========================================================================
    # 组织仓储
    # =========================================================================

    async def find_organization_by_id(self, org_id: str) -> Optional[Organization]:
        """根据ID查找组织

        Args:
            org_id: 组织标识

        Returns:
            组织实体，未找到返回None
        """
        org = self._organizations.get(org_id)
        if org is not None and org.is_deleted:
            return None
        return org

    async def find_all_organizations(
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
        orgs = [o for o in self._organizations.values() if not o.is_deleted]

        if tenant_id is not None:
            orgs = [o for o in orgs if o.tenant_id == tenant_id]

        if filters:
            if "search" in filters and filters["search"]:
                search_term = filters["search"].lower()
                orgs = [
                    o for o in orgs
                    if search_term in o.name.lower() or search_term in o.description.lower()
                ]

        if pagination.sort_by and hasattr(Organization, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            orgs.sort(key=lambda o: getattr(o, pagination.sort_by, ""), reverse=reverse)
        else:
            orgs.sort(key=lambda o: o.created_at, reverse=True)

        total = len(orgs)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = orgs[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_organization(self, entity: Organization) -> Organization:
        """保存组织

        Args:
            entity: 组织实体

        Returns:
            保存后的组织实体
        """
        self._organizations[entity.id] = entity
        logger.debug("组织已保存: id=%s", entity.id)
        return entity

    # =========================================================================
    # 项目仓储
    # =========================================================================

    async def find_project_by_id(self, project_id: str) -> Optional[Project]:
        """根据ID查找项目

        Args:
            project_id: 项目标识

        Returns:
            项目实体，未找到返回None
        """
        project = self._projects.get(project_id)
        if project is not None and project.is_deleted:
            return None
        return project

    async def find_all_projects(
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
        projects = [p for p in self._projects.values() if not p.is_deleted]

        if tenant_id is not None:
            projects = [p for p in projects if p.tenant_id == tenant_id]

        if filters:
            if "organization_id" in filters:
                projects = [p for p in projects if p.organization_id == filters["organization_id"]]
            if "environment" in filters:
                projects = [p for p in projects if p.environment.value == filters["environment"]]
            if "search" in filters and filters["search"]:
                search_term = filters["search"].lower()
                projects = [
                    p for p in projects
                    if search_term in p.name.lower() or search_term in p.description.lower()
                ]

        if pagination.sort_by and hasattr(Project, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            projects.sort(key=lambda p: getattr(p, pagination.sort_by, ""), reverse=reverse)
        else:
            projects.sort(key=lambda p: p.created_at, reverse=True)

        total = len(projects)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = projects[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_project(self, entity: Project) -> Project:
        """保存项目

        Args:
            entity: 项目实体

        Returns:
            保存后的项目实体
        """
        self._projects[entity.id] = entity
        logger.debug("项目已保存: id=%s", entity.id)
        return entity

    # =========================================================================
    # 环境仓储
    # =========================================================================

    async def find_environment_by_id(self, env_id: str) -> Optional[Environment]:
        """根据ID查找环境

        Args:
            env_id: 环境标识

        Returns:
            环境实体，未找到返回None
        """
        env = self._environments.get(env_id)
        if env is not None and env.is_deleted:
            return None
        return env

    async def find_all_environments(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[Environment]:
        """分页查询环境列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        envs = [e for e in self._environments.values() if not e.is_deleted]

        if tenant_id is not None:
            envs = [e for e in envs if e.tenant_id == tenant_id]

        if filters:
            if "project_id" in filters:
                envs = [e for e in envs if e.project_id == filters["project_id"]]
            if "environment_type" in filters:
                envs = [e for e in envs if e.environment_type.value == filters["environment_type"]]
            if "is_active" in filters:
                envs = [e for e in envs if e.is_active == filters["is_active"]]

        if pagination.sort_by and hasattr(Environment, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            envs.sort(key=lambda e: getattr(e, pagination.sort_by, ""), reverse=reverse)
        else:
            envs.sort(key=lambda e: e.created_at, reverse=True)

        total = len(envs)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = envs[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_environment(self, entity: Environment) -> Environment:
        """保存环境

        Args:
            entity: 环境实体

        Returns:
            保存后的环境实体
        """
        self._environments[entity.id] = entity
        logger.debug("环境已保存: id=%s", entity.id)
        return entity

    # =========================================================================
    # 角色分配仓储
    # =========================================================================

    async def find_role_assignment_by_id(self, assignment_id: str) -> Optional[RoleAssignment]:
        """根据ID查找角色分配

        Args:
            assignment_id: 角色分配标识

        Returns:
            角色分配实体，未找到返回None
        """
        assignment = self._role_assignments.get(assignment_id)
        if assignment is not None and assignment.is_deleted:
            return None
        return assignment

    async def find_roles_by_user(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> list[RoleAssignment]:
        """查找用户的所有角色分配

        Args:
            user_id: 用户标识
            tenant_id: 租户标识

        Returns:
            角色分配列表
        """
        assignments = [
            a for a in self._role_assignments.values()
            if a.user_id == user_id and not a.is_deleted
        ]

        if tenant_id is not None:
            assignments = [a for a in assignments if a.tenant_id == tenant_id]

        return assignments

    async def save_role_assignment(self, entity: RoleAssignment) -> RoleAssignment:
        """保存角色分配

        Args:
            entity: 角色分配实体

        Returns:
            保存后的角色分配实体
        """
        self._role_assignments[entity.id] = entity
        logger.debug("角色分配已保存: id=%s", entity.id)
        return entity

    async def delete_role_assignment(self, assignment_id: str) -> bool:
        """删除角色分配（软删除）

        Args:
            assignment_id: 角色分配标识

        Returns:
            是否删除成功
        """
        assignment = self._role_assignments.get(assignment_id)
        if assignment is None:
            return False
        assignment.mark_deleted()
        logger.debug("角色分配已删除: id=%s", assignment_id)
        return True
