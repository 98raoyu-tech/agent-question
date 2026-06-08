"""
切片实体

定义知识切片的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import ChunkStatus


@dataclass
class KnowledgeChunk(BaseEntity):
    """知识切片实体

    切片是文档经过分块处理后的最小检索单元。

    Attributes:
        document_id: 所属文档标识
        source_id: 所属知识源标识
        content: 切片内容
        chunk_index: 切片在文档中的序号
        token_count: Token数量
        embedding: 向量嵌入
        status: 切片状态
        metadata: 扩展元数据
    """

    document_id: str = ""
    source_id: str = ""
    content: str = ""
    chunk_index: int = 0
    token_count: int = 0
    embedding: list[float] = field(default_factory=list)
    status: ChunkStatus = ChunkStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_indexed(self, operator: Optional[str] = None) -> None:
        """标记为已索引

        Args:
            operator: 操作者标识
        """
        self.status = ChunkStatus.INDEXED
        self.touch(operator)

    def mark_failed(self, error: str = "", operator: Optional[str] = None) -> None:
        """标记为索引失败

        Args:
            error: 错误信息
            operator: 操作者标识
        """
        self.status = ChunkStatus.FAILED
        if error:
            self.metadata["error"] = error
        self.touch(operator)
