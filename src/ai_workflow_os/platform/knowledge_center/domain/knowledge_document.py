"""
文档实体

定义知识文档的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import DocumentStatus


@dataclass
class KnowledgeDocument(BaseEntity):
    """知识文档实体

    文档是知识源下的内容单元，经过处理后生成切片。

    Attributes:
        source_id: 所属知识源标识
        title: 文档标题
        content: 文档内容
        file_path: 文件路径
        file_size: 文件大小（字节）
        file_type: 文件类型
        status: 文档状态
        chunk_count: 切片数量
        error_message: 错误信息
        metadata: 扩展元数据
    """

    source_id: str = ""
    title: str = ""
    content: str = ""
    file_path: str = ""
    file_size: int = 0
    file_type: str = ""
    status: DocumentStatus = DocumentStatus.PENDING
    chunk_count: int = 0
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def start_processing(self, operator: Optional[str] = None) -> None:
        """开始处理文档

        Args:
            operator: 操作者标识
        """
        self.status = DocumentStatus.PROCESSING
        self.error_message = None
        self.touch(operator)

    def complete_processing(self, chunk_count: int = 0, operator: Optional[str] = None) -> None:
        """完成文档处理

        Args:
            chunk_count: 生成的切片数量
            operator: 操作者标识
        """
        self.status = DocumentStatus.COMPLETED
        self.chunk_count = chunk_count
        self.touch(operator)

    def fail_processing(self, error: str, operator: Optional[str] = None) -> None:
        """文档处理失败

        Args:
            error: 错误信息
            operator: 操作者标识
        """
        self.status = DocumentStatus.FAILED
        self.error_message = error
        self.touch(operator)

    def archive(self, operator: Optional[str] = None) -> None:
        """归档文档

        Args:
            operator: 操作者标识
        """
        self.status = DocumentStatus.ARCHIVED
        self.touch(operator)
