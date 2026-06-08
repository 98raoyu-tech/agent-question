"""
多租户枚举定义

定义租户状态、组织角色、项目角色和资源环境等枚举类型。
"""

from enum import Enum


class TenantStatus(str, Enum):
    """租户状态枚举"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class OrganizationRole(str, Enum):
    """组织角色枚举"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    """项目角色枚举"""

    LEAD = "lead"
    DEVELOPER = "developer"
    TESTER = "tester"
    VIEWER = "viewer"


class ResourceEnvironment(str, Enum):
    """资源环境枚举"""

    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PROD = "prod"
