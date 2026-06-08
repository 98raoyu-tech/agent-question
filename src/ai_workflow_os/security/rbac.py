"""
RBAC权限控制模块

基于角色的访问控制（Role-Based Access Control）实现。
提供角色管理、权限分配和访问控制检查功能。
"""

from enum import Enum
from typing import Any
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


class Role(Enum):
    """系统角色枚举
    
    定义系统中所有可用的角色类型。
    """
    ADMIN = "admin"          # 系统管理员，拥有所有权限
    OPERATOR = "operator"    # 操作员，可执行业务操作
    DEVELOPER = "developer"  # 开发者，可进行开发相关操作
    VIEWER = "viewer"        # 查看者，只有只读权限
    AGENT = "agent"          # AI Agent，自动化执行角色


class RBACManager:
    """RBAC权限管理器
    
    基于角色的访问控制系统，管理用户角色分配和资源权限。
    
    Attributes:
        roles: 角色权限映射表，键为角色，值为权限集合
        user_roles: 用户角色映射表，键为用户ID，值为角色
        resource_permissions: 资源权限映射表，键为资源名，值为允许访问的角色集合
    """
    
    def __init__(self) -> None:
        """初始化RBAC管理器"""
        # 角色权限映射：角色 -> 权限集合
        self.roles: dict[Role, set[str]] = {
            role: set() for role in Role
        }
        
        # 用户角色映射：用户ID -> 角色
        self.user_roles: dict[str, Role] = {}
        
        # 资源权限映射：资源名 -> 允许访问的角色集合
        self.resource_permissions: dict[str, set[Role]] = {}
        
        # 初始化默认权限
        self._init_default_permissions()
        
        logger.info("RBAC权限管理器已初始化")
    
    def _init_default_permissions(self) -> None:
        """初始化默认权限配置"""
        # 管理员拥有所有权限
        self.roles[Role.ADMIN] = {
            "user:create", "user:read", "user:update", "user:delete",
            "agent:create", "agent:read", "agent:update", "agent:delete",
            "tool:create", "tool:read", "tool:update", "tool:delete",
            "workflow:create", "workflow:read", "workflow:update", "workflow:delete",
            "system:config", "system:monitor", "system:audit"
        }
        
        # 操作员权限
        self.roles[Role.OPERATOR] = {
            "agent:read", "agent:update",
            "tool:read", "tool:execute",
            "workflow:read", "workflow:execute",
            "system:monitor"
        }
        
        # 开发者权限
        self.roles[Role.DEVELOPER] = {
            "agent:read", "agent:create", "agent:update",
            "tool:read", "tool:create", "tool:update",
            "workflow:read", "workflow:create", "workflow:update"
        }
        
        # 查看者权限
        self.roles[Role.VIEWER] = {
            "user:read", "agent:read", "tool:read", "workflow:read"
        }
        
        # Agent权限
        self.roles[Role.AGENT] = {
            "tool:execute", "workflow:execute",
            "agent:read", "tool:read"
        }
    
    def assign_role(self, user_id: str, role: Role) -> None:
        """分配角色给用户
        
        Args:
            user_id: 用户ID
            role: 要分配的角色
        """
        # 检查用户是否已有角色
        if user_id in self.user_roles:
            old_role = self.user_roles[user_id]
            logger.info(f"用户 '{user_id}' 角色从 {old_role.value} 更新为 {role.value}")
        else:
            logger.info(f"已为用户 '{user_id}' 分配角色: {role.value}")
        
        self.user_roles[user_id] = role
    
    def revoke_role(self, user_id: str, role: Role) -> bool:
        """撤销用户角色
        
        Args:
            user_id: 用户ID
            role: 要撤销的角色
            
        Returns:
            bool: 撤销成功返回True，用户不存在或角色不匹配返回False
        """
        # 检查用户是否存在
        if user_id not in self.user_roles:
            logger.warning(f"用户 '{user_id}' 不存在")
            return False
        
        # 检查角色是否匹配
        if self.user_roles[user_id] != role:
            logger.warning(f"用户 '{user_id}' 的角色不是 {role.value}")
            return False
        
        # 撤销角色
        del self.user_roles[user_id]
        logger.info(f"已撤销用户 '{user_id}' 的角色: {role.value}")
        return True
    
    def check_access(self, user_id: str, resource: str, action: str) -> bool:
        """检查用户是否有权访问资源
        
        Args:
            user_id: 用户ID
            resource: 资源名称
            action: 操作类型（如 create, read, update, delete）
            
        Returns:
            bool: 有权限返回True，否则返回False
        """
        # 获取用户角色
        user_role = self.user_roles.get(user_id)
        
        # 用户不存在或没有角色
        if not user_role:
            logger.warning(f"用户 '{user_id}' 不存在或未分配角色")
            return False
        
        # 构建权限字符串
        permission = f"{resource}:{action}"
        
        # 检查角色是否有该权限
        if self._role_has_permission(user_role, resource, action):
            logger.debug(f"用户 '{user_id}' 有权执行 {permission}")
            return True
        
        # 检查资源级别的权限
        if resource in self.resource_permissions:
            if user_role in self.resource_permissions[resource]:
                logger.debug(f"用户 '{user_id}' 通过资源权限有权访问 {resource}")
                return True
        
        logger.warning(f"用户 '{user_id}' 无权执行 {permission}")
        return False
    
    def add_permission(self, role: Role, resource: str, action: str) -> None:
        """为角色添加权限
        
        Args:
            role: 角色
            resource: 资源名称
            action: 操作类型
        """
        # 构建权限字符串
        permission = f"{resource}:{action}"
        
        # 添加权限
        self.roles[role].add(permission)
        
        logger.info(f"已为角色 {role.value} 添加权限: {permission}")
    
    def get_user_permissions(self, user_id: str) -> dict[str, Any]:
        """获取用户权限信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户权限信息，包含角色和权限列表
        """
        # 获取用户角色
        user_role = self.user_roles.get(user_id)
        
        if not user_role:
            return {
                "user_id": user_id,
                "role": None,
                "permissions": [],
                "exists": False
            }
        
        # 获取角色权限
        permissions = list(self.roles.get(user_role, set()))
        
        return {
            "user_id": user_id,
            "role": user_role.value,
            "permissions": sorted(permissions),
            "exists": True
        }
    
    def _role_has_permission(self, role: Role, resource: str, action: str) -> bool:
        """检查角色是否有指定权限
        
        Args:
            role: 角色
            resource: 资源名称
            action: 操作类型
            
        Returns:
            bool: 有权限返回True
        """
        # 构建权限字符串
        permission = f"{resource}:{action}"
        
        # 检查角色权限集合
        role_permissions = self.roles.get(role, set())
        
        # 检查精确匹配
        if permission in role_permissions:
            return True
        
        # 检查通配符权限（如 resource:* 表示该资源的所有操作）
        wildcard_permission = f"{resource}:*"
        if wildcard_permission in role_permissions:
            return True
        
        # 检查全局通配符（*:* 表示所有权限）
        if "*:*" in role_permissions:
            return True
        
        return False
    
    def get_all_roles(self) -> list[dict[str, Any]]:
        """获取所有角色信息
        
        Returns:
            list: 角色信息列表
        """
        roles_info = []
        
        for role in Role:
            permissions = list(self.roles.get(role, set()))
            roles_info.append({
                "role": role.value,
                "permissions": sorted(permissions),
                "permission_count": len(permissions)
            })
        
        return roles_info
    
    def get_users_by_role(self, role: Role) -> list[str]:
        """获取指定角色的所有用户
        
        Args:
            role: 角色
            
        Returns:
            list: 用户ID列表
        """
        return [
            user_id for user_id, user_role in self.user_roles.items()
            if user_role == role
        ]
    
    def get_statistics(self) -> dict[str, Any]:
        """获取RBAC统计信息
        
        Returns:
            dict: 统计信息
        """
        # 统计各角色的用户数量
        role_counts: dict[str, int] = {}
        for role in Role:
            count = len(self.get_users_by_role(role))
            role_counts[role.value] = count
        
        return {
            "total_users": len(self.user_roles),
            "total_roles": len(Role),
            "role_distribution": role_counts,
            "total_resources": len(self.resource_permissions)
        }
    
    def add_resource_permission(self, resource: str, roles: list[Role]) -> None:
        """添加资源权限
        
        Args:
            resource: 资源名称
            roles: 允许访问的角色列表
        """
        self.resource_permissions[resource] = set(roles)
        logger.info(f"已添加资源 '{resource}' 的权限，允许角色: {[r.value for r in roles]}")
    
    def remove_resource_permission(self, resource: str) -> bool:
        """移除资源权限
        
        Args:
            resource: 资源名称
            
        Returns:
            bool: 移除成功返回True，资源不存在返回False
        """
        if resource not in self.resource_permissions:
            logger.warning(f"资源 '{resource}' 的权限配置不存在")
            return False
        
        del self.resource_permissions[resource]
        logger.info(f"已移除资源 '{resource}' 的权限配置")
        return True