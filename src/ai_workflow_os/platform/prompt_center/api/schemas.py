"""
Prompt中心请求/响应Schema

定义Prompt模板相关的API请求和响应数据模型。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import PromptCategory, PromptStatus


# =============================================================================
# 请求Schema
# =============================================================================


class CreatePromptRequest(CreateDTO):
    """创建Prompt模板请求"""

    name: str = Field(min_length=1, max_length=200, description="模板名称")
    description: str = Field(default="", max_length=2000, description="模板描述")
    content: str = Field(description="模板内容")
    category: PromptCategory = Field(default=PromptCategory.TEMPLATE, description="模板分类")
    variables: list[dict[str, Any]] = Field(default_factory=list, description="变量定义列表")
    model_compatibility: list[str] = Field(default_factory=list, description="兼容的模型列表")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class UpdatePromptRequest(UpdateDTO):
    """更新Prompt模板请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="模板描述")
    content: Optional[str] = Field(default=None, description="模板内容")
    category: Optional[PromptCategory] = Field(default=None, description="模板分类")
    variables: Optional[list[dict[str, Any]]] = Field(default=None, description="变量定义列表")
    model_compatibility: Optional[list[str]] = Field(default=None, description="兼容的模型列表")
    tags: Optional[list[str]] = Field(default=None, description="标签列表")


# =============================================================================
# 响应Schema
# =============================================================================


class PromptResponse(BaseDTO):
    """Prompt模板响应"""

    name: str = Field(description="模板名称")
    description: str = Field(description="模板描述")
    content: str = Field(description="模板内容")
    category: PromptCategory = Field(description="模板分类")
    status: PromptStatus = Field(description="模板状态")
    variables: list[dict[str, Any]] = Field(description="变量定义列表")
    model_compatibility: list[str] = Field(description="兼容的模型列表")
    usage_count: int = Field(description="使用次数")
    tags: list[str] = Field(description="标签列表")


class PromptListResponse(BaseModel):
    """Prompt模板列表响应"""

    items: list[PromptResponse] = Field(description="模板列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
