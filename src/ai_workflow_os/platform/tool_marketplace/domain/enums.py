"""
工具市场枚举定义

定义工具类型和状态等枚举。
"""

from enum import Enum


class ToolType(str, Enum):
    """工具类型枚举"""

    REST = "rest"
    """REST API工具"""

    MCP = "mcp"
    """MCP工具"""

    PYTHON = "python"
    """Python函数工具"""

    SQL = "sql"
    """SQL查询工具"""

    SHELL = "shell"
    """Shell命令工具"""

    GRAPHQL = "graphql"
    """GraphQL工具"""

    GRPC = "grpc"
    """gRPC工具"""


class ToolStatus(str, Enum):
    """工具状态枚举"""

    DRAFT = "draft"
    """草稿状态"""

    PUBLISHED = "published"
    """已发布状态"""

    DEPRECATED = "deprecated"
    """已废弃状态"""
