"""
知识源实体

定义知识源的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import SourceType


@dataclass
class KnowledgeSource(BaseEntity):
    """知识源实体

    知识源是知识库的顶层组织单元，包含多个文档。

    Attributes:
        name: 知识源名称
        description: 知识源描述
        source_type: 知识源类型
        config: 知识源配置
        document_count: 文档数量
        total_chunks: 总切片数
        is_enabled: 是否启用
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    source_type: SourceType = SourceType.PDF
    config: dict[str, Any] = field(default_factory=dict)
    document_count: int = 0
    total_chunks: int = 0
    is_enabled: bool = True
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def enable(self, operator: Optional[str] = None) -> None:
        """启用知识源

        Args:
            operator: 操作者标识
        """
        self.is_enabled = True
        self.touch(operator)

    def disable(self, operator: Optional[str] = None) -> None:
        """禁用知识源

        Args:
            operator: 操作者标识
        """
        self.is_enabled = False
        self.touch(operator)

    def increment_document_count(self, operator: Optional[str] = None) -> None:
        """增加文档计数

        Args:
            operator: 操作者标识
        """
        self.document_count += 1
        self.touch(operator)

    def decrement_document_count(self, operator: Optional[str] = None) -> None:
        """减少文档计数

        Args:
            operator: 操作者标识
        """
        if self.document_count > 0:
            self.document_count -= 1
        self.touch(operator)

    def update_chunk_count(self, count: int, operator: Optional[str] = None) -> None:
        """更新切片计数

        Args:
            count: 新的切片总数
            operator: 操作者标识
        """
        self.total_chunks = count
        self.touch(operator)
