"""
多租户请求/响应Schema

定义租户、组织、项目、环境和RBAC相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import (
    OrganizationRole,
    ProjectRole,
    ResourceEnvironment,
    TenantStatus,
)


# =============================================================================
# 租户Schema
# =============================================================================


class CreateTenantRequest(CreateDTO):
    """创建租户请求"""

    name: str = Field(min_length=1, max_length=200, description="租户名称")
    slug: str = Field(min_length=1, max_length=100, pattern="^[a-z0-9-]+$", description="租户唯一标识符")
    plan: str = Field(default="free", description="套餐类型")
    settings: dict[str, Any] = Field(default_factory=dict, description="租户配置")
    max_users: int = Field(default=10, ge=1, description="最大用户数")
    max_agents: int = Field(default=5, ge=1, description="最大Agent数")
    max_projects: int = Field(default=3, ge=1, description="最大项目数")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class UpdateTenantRequest(UpdateDTO):
    """更新租户请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="租户名称")
    plan: Optional[str] = Field(default=None, description="套餐类型")
    settings: Optional[dict[str, Any]] = Field(default=None, description="租户配置")
    max_users: Optional[int] = Field(default=None, ge=1, description="最大用户数")
    max_agents: Optional[int] = Field(default=None, ge=1, description="最大Agent数")
    max_projects: Optional[int] = Field(default=None, ge=1, description="最大项目数")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="扩展元数据")


class TenantResponse(BaseDTO):
    """租户响应"""

    name: str = Field(description="租户名称")
    slug: str = Field(description="租户唯一标识符")
    status: TenantStatus = Field(description="租户状态")
    plan: str = Field(description="套餐类型")
    settings: dict[str, Any] = Field(description="租户配置")
    max_users: int = Field(description="最大用户数")
    max_agents: int = Field(description="最大Agent数")
    max_projects: int = Field(description="最大项目数")


class TenantListResponse(BaseModel):
    """租户列表响应"""

    items: list[TenantResponse] = Field(description="租户列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 组织Schema
# =============================================================================


class CreateOrganizationRequest(CreateDTO):
    """创建组织请求"""

    name: str = Field(min_length=1, max_length=200, description="组织名称")
    description: str = Field(default="", max_length=2000, description="组织描述")
    owner_id: str = Field(description="组织拥有者标识")
    settings: dict[str, Any] = Field(default_factory=dict, description="组织配置")


class OrganizationResponse(BaseDTO):
    """组织响应"""

    name: str = Field(description="组织名称")
    description: str = Field(description="组织描述")
    owner_id: str = Field(description="组织拥有者标识")
    member_ids: list[str] = Field(description="成员标识列表")


class OrganizationListResponse(BaseModel):
    """组织列表响应"""

    items: list[OrganizationResponse] = Field(description="组织列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 项目Schema
# =============================================================================


class CreateProjectRequest(CreateDTO):
    """创建项目请求"""

    organization_id: str = Field(description="所属组织标识")
    name: str = Field(min_length=1, max_length=200, description="项目名称")
    description: str = Field(default="", max_length=2000, description="项目描述")
    environment: ResourceEnvironment = Field(default=ResourceEnvironment.DEV, description="项目环境")
    owner_id: str = Field(description="项目拥有者标识")
    settings: dict[str, Any] = Field(default_factory=dict, description="项目配置")


class ProjectResponse(BaseDTO):
    """项目响应"""

    organization_id: str = Field(description="所属组织标识")
    name: str = Field(description="项目名称")
    description: str = Field(description="项目描述")
    environment: ResourceEnvironment = Field(description="项目环境")
    owner_id: str = Field(description="项目拥有者标识")
    member_roles: dict[str, ProjectRole] = Field(description="成员角色映射")
    agent_ids: list[str] = Field(description="关联Agent标识列表")


class ProjectListResponse(BaseModel):
    """项目列表响应"""

    items: list[ProjectResponse] = Field(description="项目列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 环境Schema
# =============================================================================


class CreateEnvironmentRequest(CreateDTO):
    """创建环境请求"""

    project_id: str = Field(description="所属项目标识")
    name: str = Field(min_length=1, max_length=200, description="环境名称")
    environment_type: ResourceEnvironment = Field(description="环境类型")
    config: dict[str, Any] = Field(default_factory=dict, description="环境配置")


class EnvironmentResponse(BaseDTO):
    """环境响应"""

    project_id: str = Field(description="所属项目标识")
    name: str = Field(description="环境名称")
    environment_type: ResourceEnvironment = Field(description="环境类型")
    config: dict[str, Any] = Field(description="环境配置")
    is_active: bool = Field(description="是否激活")
    deployed_agent_ids: list[str] = Field(description="已部署Agent标识列表")


class EnvironmentListResponse(BaseModel):
    """环境列表响应"""

    items: list[EnvironmentResponse] = Field(description="环境列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# RBAC Schema
# =============================================================================


class AssignRoleRequest(CreateDTO):
    """分配角色请求"""

    user_id: str = Field(description="用户标识")
    role: OrganizationRole = Field(description="组织角色")
    scope_type: str = Field(pattern="^(tenant|organization|project)$", description="作用域类型")
    scope_id: str = Field(description="作用域标识")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")


class RoleAssignmentResponse(BaseDTO):
    """角色分配响应"""

    user_id: str = Field(description="用户标识")
    role: OrganizationRole = Field(description="组织角色")
    scope_type: str = Field(description="作用域类型")
    scope_id: str = Field(description="作用域标识")
    granted_by: str = Field(description="授权者标识")
    granted_at: datetime = Field(description="授权时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")


class RoleAssignmentListResponse(BaseModel):
    """角色分配列表响应"""

    items: list[RoleAssignmentResponse] = Field(description="角色分配列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""

    user_id: str = Field(description="用户标识")
    roles: list[RoleAssignmentResponse] = Field(description="角色列表")
