"""
安全模块

提供RBAC权限控制、策略引擎、Prompt注入防御和审计日志功能。
该模块是AI Workflow OS的安全核心，负责系统的访问控制和安全防护。
"""

from .rbac import RBACManager, Role
from .policy_engine import PolicyEngine, PolicyRule, PolicyAction, PolicyResult
from .prompt_firewall import (
    PromptFirewall,
    InjectionPattern,
    FirewallResult,
    InjectionMatch
)
from .audit import AuditLogger, AuditEntry

__all__ = [
    # RBAC权限控制
    "RBACManager",
    "Role",
    
    # 策略引擎
    "PolicyEngine",
    "PolicyRule",
    "PolicyAction",
    "PolicyResult",
    
    # Prompt注入防御
    "PromptFirewall",
    "InjectionPattern",
    "FirewallResult",
    "InjectionMatch",
    
    # 审计日志
    "AuditLogger",
    "AuditEntry",
]