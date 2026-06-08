"""
审计日志实体

定义审计日志的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import AuditAction


@dataclass
class AuditLog(BaseEntity):
    """审计日志实体

    记录平台操作的审计信息。

    Attributes:
        user_id: 操作用户标识
        action: 审计动作
        resource_type: 资源类型
        resource_id: 资源标识
        details: 操作详情
        ip_address: IP地址
        user_agent: 用户代理
        success: 操作是否成功
        error_message: 错误信息
    """

    user_id: str = ""
    action: AuditAction = AuditAction.READ
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    success: bool = True
    error_message: Optional[str] = None
