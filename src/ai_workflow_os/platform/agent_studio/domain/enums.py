"""
Agent Studio枚举定义

定义Agent相关的枚举类型，包括Agent类型和状态。
"""

from enum import Enum


class AgentType(str, Enum):
    """Agent类型枚举"""

    SINGLE = "single"
    """单Agent模式"""

    MULTI = "multi"
    """多Agent协作模式"""

    TEAM = "team"
    """团队Agent模式"""

    WORKFLOW = "workflow"
    """工作流Agent模式"""


class AgentStatus(str, Enum):
    """Agent状态枚举"""

    DRAFT = "draft"
    """草稿状态"""

    PUBLISHED = "published"
    """已发布状态"""

    ARCHIVED = "archived"
    """已归档状态"""

    DEPRECATED = "deprecated"
    """已废弃状态"""
