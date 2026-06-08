"""
多租户FastAPI路由

提供租户、组织、项目、环境和RBAC管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.multi_tenant_service import MultiTenantService
from ..domain.enums import OrganizationRole, ProjectRole, ResourceEnvironment
from ..domain.environment import Environment
from ..domain.organization import Organization
from ..domain.project import Project
from ..domain.rbac import RoleAssignment
from ..domain.tenant import Tenant
from ..infrastructure.multi_tenant_repository import MultiTenantRepository
from .schemas import (
    AssignRoleRequest,
    CreateEnvironmentRequest,
    CreateOrganizationRequest,
    CreateProjectRequest,
    CreateTenantRequest,
    EnvironmentListResponse,
    EnvironmentResponse,
    OrganizationListResponse,
    OrganizationResponse,
    ProjectListResponse,
    ProjectResponse,
    RoleAssignmentListResponse,
    RoleAssignmentResponse,
    TenantListResponse,
    TenantResponse,
    UpdateTenantRequest,
    UserPermissionsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multi-tenant", tags=["Multi-Tenant"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_multi_tenant_repository = MultiTenantRepository()
_multi_tenant_service = MultiTenantService(_multi_tenant_repository)


# =============================================================================
# 租户端点
# =============================================================================


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建租户",
    description="创建一个新的租户",
)
async def create_tenant(request: CreateTenantRequest) -> TenantResponse:
    """创建租户

    Args:
        request: 创建租户请求

    Returns:
        创建的租户响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        tenant = Tenant(
            name=request.name,
            slug=request.slug,
            plan=request.plan,
            settings=request.settings,
            max_users=request.max_users,
            max_agents=request.max_agents,
            max_projects=request.max_projects,
            metadata=request.metadata,
            tenant_id=request.tenant_id,
        )

        created_tenant = await _multi_tenant_service.create_tenant(tenant, request.created_by)
        return _to_tenant_response(created_tenant)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="获取租户详情",
    description="根据ID获取租户的详细信息",
)
async def get_tenant(tenant_id: str) -> TenantResponse:
    """获取租户详情

    Args:
        tenant_id: 租户标识

    Returns:
        租户响应

    Raises:
        HTTPException: 租户不存在
    """
    try:
        tenant = await _multi_tenant_service.get_tenant(tenant_id)
        return _to_tenant_response(tenant)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tenants",
    response_model=TenantListResponse,
    summary="查询租户列表",
    description="分页查询租户列表",
)
async def list_tenants(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="状态过滤"),
    plan: Optional[str] = Query(default=None, description="套餐过滤"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
) -> TenantListResponse:
    """查询租户列表

    Args:
        page: 页码
        page_size: 每页大小
        status_filter: 状态过滤
        plan: 套餐过滤
        search: 搜索关键词

    Returns:
        租户列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if plan:
        filters["plan"] = plan
    if search:
        filters["search"] = search

    result = await _multi_tenant_service.list_tenants(pagination, filters)

    return TenantListResponse(
        items=[_to_tenant_response(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="更新租户",
    description="更新租户信息",
)
async def update_tenant(tenant_id: str, request: UpdateTenantRequest) -> TenantResponse:
    """更新租户

    Args:
        tenant_id: 租户标识
        request: 更新租户请求

    Returns:
        更新后的租户响应

    Raises:
        HTTPException: 更新失败
    """
    try:
        existing_tenant = await _multi_tenant_service.get_tenant(tenant_id)

        if request.name is not None:
            existing_tenant.name = request.name
        if request.plan is not None:
            existing_tenant.plan = request.plan
        if request.settings is not None:
            existing_tenant.settings = request.settings
        if request.max_users is not None:
            existing_tenant.max_users = request.max_users
        if request.max_agents is not None:
            existing_tenant.max_agents = request.max_agents
        if request.max_projects is not None:
            existing_tenant.max_projects = request.max_projects
        if request.metadata is not None:
            existing_tenant.metadata = request.metadata

        updated_tenant = await _multi_tenant_service.update_tenant(
            tenant_id, existing_tenant, request.updated_by
        )
        return _to_tenant_response(updated_tenant)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 组织端点
# =============================================================================


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建组织",
    description="创建一个新的组织",
)
async def create_organization(request: CreateOrganizationRequest) -> OrganizationResponse:
    """创建组织

    Args:
        request: 创建组织请求

    Returns:
        创建的组织响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        organization = Organization(
            tenant_id=request.tenant_id,
            name=request.name,
            description=request.description,
            owner_id=request.owner_id,
            settings=request.settings,
        )

        created_org = await _multi_tenant_service.create_organization(organization, request.created_by)
        return _to_organization_response(created_org)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/organizations/{organization_id}",
    response_model=OrganizationResponse,
    summary="获取组织详情",
    description="根据ID获取组织的详细信息",
)
async def get_organization(organization_id: str) -> OrganizationResponse:
    """获取组织详情

    Args:
        organization_id: 组织标识

    Returns:
        组织响应

    Raises:
        HTTPException: 组织不存在
    """
    try:
        org = await _multi_tenant_service.get_organization(organization_id)
        return _to_organization_response(org)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/organizations",
    response_model=OrganizationListResponse,
    summary="查询组织列表",
    description="分页查询组织列表",
)
async def list_organizations(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
) -> OrganizationListResponse:
    """查询组织列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识
        search: 搜索关键词

    Returns:
        组织列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    filters = {}
    if search:
        filters["search"] = search

    result = await _multi_tenant_service.list_organizations(pagination, tenant_id, filters)

    return OrganizationListResponse(
        items=[_to_organization_response(o) for o in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 项目端点
# =============================================================================


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
    description="创建一个新的项目",
)
async def create_project(request: CreateProjectRequest) -> ProjectResponse:
    """创建项目

    Args:
        request: 创建项目请求

    Returns:
        创建的项目响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        project = Project(
            tenant_id=request.tenant_id,
            organization_id=request.organization_id,
            name=request.name,
            description=request.description,
            environment=request.environment,
            owner_id=request.owner_id,
            settings=request.settings,
        )

        created_project = await _multi_tenant_service.create_project(project, request.created_by)
        return _to_project_response(created_project)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="获取项目详情",
    description="根据ID获取项目的详细信息",
)
async def get_project(project_id: str) -> ProjectResponse:
    """获取项目详情

    Args:
        project_id: 项目标识

    Returns:
        项目响应

    Raises:
        HTTPException: 项目不存在
    """
    try:
        project = await _multi_tenant_service.get_project(project_id)
        return _to_project_response(project)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/projects",
    response_model=ProjectListResponse,
    summary="查询项目列表",
    description="分页查询项目列表",
)
async def list_projects(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
    organization_id: Optional[str] = Query(default=None, description="组织标识"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
) -> ProjectListResponse:
    """查询项目列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识
        organization_id: 组织标识
        search: 搜索关键词

    Returns:
        项目列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    filters = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if search:
        filters["search"] = search

    result = await _multi_tenant_service.list_projects(pagination, tenant_id, filters)

    return ProjectListResponse(
        items=[_to_project_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 环境端点
# =============================================================================


@router.post(
    "/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建环境",
    description="创建一个新的环境",
)
async def create_environment(request: CreateEnvironmentRequest) -> EnvironmentResponse:
    """创建环境

    Args:
        request: 创建环境请求

    Returns:
        创建的环境响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        environment = Environment(
            tenant_id=request.tenant_id,
            project_id=request.project_id,
            name=request.name,
            environment_type=request.environment_type,
            config=request.config,
        )

        created_env = await _multi_tenant_service.create_environment(environment, request.created_by)
        return _to_environment_response(created_env)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/environments",
    response_model=EnvironmentListResponse,
    summary="查询环境列表",
    description="分页查询环境列表",
)
async def list_environments(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
    project_id: Optional[str] = Query(default=None, description="项目标识"),
) -> EnvironmentListResponse:
    """查询环境列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识
        project_id: 项目标识

    Returns:
        环境列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _multi_tenant_service.list_environments(pagination, tenant_id, project_id)

    return EnvironmentListResponse(
        items=[_to_environment_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# RBAC端点
# =============================================================================


@router.post(
    "/roles",
    response_model=RoleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分配角色",
    description="为用户分配角色",
)
async def assign_role(request: AssignRoleRequest) -> RoleAssignmentResponse:
    """分配角色

    Args:
        request: 分配角色请求

    Returns:
        角色分配响应

    Raises:
        HTTPException: 分配失败
    """
    try:
        role_assignment = RoleAssignment(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            role=request.role,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            expires_at=request.expires_at,
        )

        created_assignment = await _multi_tenant_service.assign_role(
            role_assignment, request.created_by
        )
        return _to_role_assignment_response(created_assignment)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/roles",
    response_model=RoleAssignmentListResponse,
    summary="查询角色列表",
    description="分页查询角色分配列表",
)
async def list_roles(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
    user_id: Optional[str] = Query(default=None, description="用户标识"),
) -> RoleAssignmentListResponse:
    """查询角色列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识
        user_id: 用户标识

    Returns:
        角色分配列表响应
    """
    if user_id:
        roles = await _multi_tenant_service.get_user_roles(user_id, tenant_id)
        paginated_roles = roles[:page_size]
        return RoleAssignmentListResponse(
            items=[_to_role_assignment_response(r) for r in paginated_roles],
            total=len(roles),
            page=page,
            page_size=page_size,
        )

    return RoleAssignmentListResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="撤销角色",
    description="撤销指定的角色分配",
)
async def revoke_role(role_id: str) -> None:
    """撤销角色

    Args:
        role_id: 角色分配标识

    Raises:
        HTTPException: 撤销失败
    """
    try:
        await _multi_tenant_service.revoke_role(role_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    summary="获取用户权限",
    description="获取指定用户的所有角色权限",
)
async def get_user_permissions(
    user_id: str,
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> UserPermissionsResponse:
    """获取用户权限

    Args:
        user_id: 用户标识
        tenant_id: 租户标识

    Returns:
        用户权限响应
    """
    roles = await _multi_tenant_service.get_user_roles(user_id, tenant_id)

    return UserPermissionsResponse(
        user_id=user_id,
        roles=[_to_role_assignment_response(r) for r in roles],
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_tenant_response(tenant: Tenant) -> TenantResponse:
    """将租户实体转换为响应Schema

    Args:
        tenant: 租户实体

    Returns:
        租户响应
    """
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        plan=tenant.plan,
        settings=tenant.settings,
        max_users=tenant.max_users,
        max_agents=tenant.max_agents,
        max_projects=tenant.max_projects,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        tenant_id=tenant.tenant_id,
    )


def _to_organization_response(org: Organization) -> OrganizationResponse:
    """将组织实体转换为响应Schema

    Args:
        org: 组织实体

    Returns:
        组织响应
    """
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        description=org.description,
        owner_id=org.owner_id,
        member_ids=org.member_ids,
        created_at=org.created_at,
        updated_at=org.updated_at,
        tenant_id=org.tenant_id,
    )


def _to_project_response(project: Project) -> ProjectResponse:
    """将项目实体转换为响应Schema

    Args:
        project: 项目实体

    Returns:
        项目响应
    """
    return ProjectResponse(
        id=project.id,
        organization_id=project.organization_id,
        name=project.name,
        description=project.description,
        environment=project.environment,
        owner_id=project.owner_id,
        member_roles=project.member_roles,
        agent_ids=project.agent_ids,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tenant_id=project.tenant_id,
    )


def _to_environment_response(env: Environment) -> EnvironmentResponse:
    """将环境实体转换为响应Schema

    Args:
        env: 环境实体

    Returns:
        环境响应
    """
    return EnvironmentResponse(
        id=env.id,
        project_id=env.project_id,
        name=env.name,
        environment_type=env.environment_type,
        config=env.config,
        is_active=env.is_active,
        deployed_agent_ids=env.deployed_agent_ids,
        created_at=env.created_at,
        updated_at=env.updated_at,
        tenant_id=env.tenant_id,
    )


def _to_role_assignment_response(assignment: RoleAssignment) -> RoleAssignmentResponse:
    """将角色分配实体转换为响应Schema

    Args:
        assignment: 角色分配实体

    Returns:
        角色分配响应
    """
    return RoleAssignmentResponse(
        id=assignment.id,
        user_id=assignment.user_id,
        role=assignment.role,
        scope_type=assignment.scope_type,
        scope_id=assignment.scope_id,
        granted_by=assignment.granted_by,
        granted_at=assignment.granted_at,
        expires_at=assignment.expires_at,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        tenant_id=assignment.tenant_id,
    )
