"""
治理中心枚举定义

定义策略类型、状态和审计动作等枚举。
"""

from enum import Enum


class PolicyType(str, Enum):
    """策略类型枚举"""

    ACCESS_CONTROL = "access_control"
    """访问控制策略"""

    DATA_PRIVACY = "data_privacy"
    """数据隐私策略"""

    COST_CONTROL = "cost_control"
    """成本控制策略"""

    SAFETY = "safety"
    """安全策略"""

    COMPLIANCE = "compliance"
    """合规策略"""


class PolicyStatus(str, Enum):
    """策略状态枚举"""

    DRAFT = "draft"
    """草稿状态"""

    ACTIVE = "active"
    """激活状态"""

    DISABLED = "disabled"
    """禁用状态"""


class AuditAction(str, Enum):
    """审计动作枚举"""

    CREATE = "create"
    """创建"""

    READ = "read"
    """读取"""

    UPDATE = "update"
    """更新"""

    DELETE = "delete"
    """删除"""

    PUBLISH = "publish"
    """发布"""

    EXECUTE = "execute"
    """执行"""

    LOGIN = "login"
    """登录"""

    LOGOUT = "logout"
    """登出"""
