"""
Prompt中心枚举定义

定义Prompt分类和状态等枚举。
"""

from enum import Enum


class PromptCategory(str, Enum):
    """Prompt分类枚举"""

    SYSTEM = "system"
    """系统提示词"""

    USER = "user"
    """用户提示词"""

    TEMPLATE = "template"
    """模板提示词"""

    CHAIN = "chain"
    """链式提示词"""


class PromptStatus(str, Enum):
    """Prompt状态枚举"""

    DRAFT = "draft"
    """草稿状态"""

    ACTIVE = "active"
    """激活状态"""

    ARCHIVED = "archived"
    """已归档状态"""
