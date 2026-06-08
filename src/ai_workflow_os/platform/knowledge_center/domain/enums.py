"""
知识中心枚举定义

定义知识源类型和文档状态等枚举。
"""

from enum import Enum


class SourceType(str, Enum):
    """知识源类型枚举"""

    PDF = "pdf"
    """PDF文档"""

    WORD = "word"
    """Word文档"""

    WEB = "web"
    """网页"""

    CONFLUENCE = "confluence"
    """Confluence文档"""

    NOTION = "notion"
    """Notion文档"""

    GITHUB = "github"
    """GitHub仓库"""

    DATABASE = "database"
    """数据库"""

    API = "api"
    """API接口"""

    MARKDOWN = "markdown"
    """Markdown文档"""


class DocumentStatus(str, Enum):
    """文档状态枚举"""

    PENDING = "pending"
    """待处理"""

    PROCESSING = "processing"
    """处理中"""

    COMPLETED = "completed"
    """处理完成"""

    FAILED = "failed"
    """处理失败"""

    ARCHIVED = "archived"
    """已归档"""


class ChunkStatus(str, Enum):
    """切片状态枚举"""

    PENDING = "pending"
    """待索引"""

    INDEXED = "indexed"
    """已索引"""

    FAILED = "failed"
    """索引失败"""
