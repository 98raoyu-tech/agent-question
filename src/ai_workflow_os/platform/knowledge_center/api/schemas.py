"""
知识中心请求/响应Schema

定义知识源和文档相关的API请求和响应数据模型。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import DocumentStatus, SourceType


# =============================================================================
# 知识源Schema
# =============================================================================


class CreateSourceRequest(CreateDTO):
    """创建知识源请求"""

    name: str = Field(min_length=1, max_length=200, description="知识源名称")
    description: str = Field(default="", max_length=2000, description="知识源描述")
    source_type: SourceType = Field(description="知识源类型")
    config: dict[str, Any] = Field(default_factory=dict, description="知识源配置")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class SourceResponse(BaseDTO):
    """知识源响应"""

    name: str = Field(description="知识源名称")
    description: str = Field(description="知识源描述")
    source_type: SourceType = Field(description="知识源类型")
    document_count: int = Field(description="文档数量")
    total_chunks: int = Field(description="总切片数")
    is_enabled: bool = Field(description="是否启用")
    tags: list[str] = Field(description="标签列表")


class SourceListResponse(BaseModel):
    """知识源列表响应"""

    items: list[SourceResponse] = Field(description="知识源列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 文档Schema
# =============================================================================


class CreateDocumentRequest(CreateDTO):
    """创建文档请求"""

    source_id: str = Field(description="所属知识源标识")
    title: str = Field(min_length=1, max_length=500, description="文档标题")
    content: str = Field(default="", description="文档内容")
    file_path: str = Field(default="", description="文件路径")
    file_size: int = Field(default=0, description="文件大小（字节）")
    file_type: str = Field(default="", description="文件类型")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class DocumentResponse(BaseDTO):
    """文档响应"""

    source_id: str = Field(description="所属知识源标识")
    title: str = Field(description="文档标题")
    content: str = Field(description="文档内容")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小（字节）")
    file_type: str = Field(description="文件类型")
    status: DocumentStatus = Field(description="文档状态")
    chunk_count: int = Field(description="切片数量")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class DocumentListResponse(BaseModel):
    """文档列表响应"""

    items: list[DocumentResponse] = Field(description="文档列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
