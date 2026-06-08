"""
工具市场请求/响应Schema

定义工具相关的API请求和响应数据模型。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import ToolStatus, ToolType


# =============================================================================
# 请求Schema
# =============================================================================


class CreateToolRequest(CreateDTO):
    """创建工具定义请求"""

    name: str = Field(min_length=1, max_length=200, description="工具名称")
    description: str = Field(default="", max_length=2000, description="工具描述")
    tool_type: ToolType = Field(description="工具类型")
    endpoint: str = Field(description="工具端点")
    parameters: dict[str, Any] = Field(default_factory=dict, description="参数定义")
    return_type: dict[str, Any] = Field(default_factory=dict, description="返回类型定义")
    authentication: dict[str, Any] = Field(default_factory=dict, description="认证配置")
    timeout: int = Field(default=30, ge=1, description="超时时间（秒）")
    retry_count: int = Field(default=3, ge=0, description="重试次数")
    author: str = Field(default="", description="作者")
    version: str = Field(default="1.0.0", description="版本号")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class UpdateToolRequest(UpdateDTO):
    """更新工具定义请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="工具名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="工具描述")
    tool_type: Optional[ToolType] = Field(default=None, description="工具类型")
    endpoint: Optional[str] = Field(default=None, description="工具端点")
    parameters: Optional[dict[str, Any]] = Field(default=None, description="参数定义")
    return_type: Optional[dict[str, Any]] = Field(default=None, description="返回类型定义")
    authentication: Optional[dict[str, Any]] = Field(default=None, description="认证配置")
    timeout: Optional[int] = Field(default=None, ge=1, description="超时时间（秒）")
    retry_count: Optional[int] = Field(default=None, ge=0, description="重试次数")
    author: Optional[str] = Field(default=None, description="作者")
    tags: Optional[list[str]] = Field(default=None, description="标签列表")


# =============================================================================
# 响应Schema
# =============================================================================


class ToolResponse(BaseDTO):
    """工具定义响应"""

    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    tool_type: ToolType = Field(description="工具类型")
    status: ToolStatus = Field(description="工具状态")
    endpoint: str = Field(description="工具端点")
    parameters: dict[str, Any] = Field(description="参数定义")
    return_type: dict[str, Any] = Field(description="返回类型定义")
    timeout: int = Field(description="超时时间（秒）")
    retry_count: int = Field(description="重试次数")
    usage_count: int = Field(description="使用次数")
    author: str = Field(description="作者")
    version: str = Field(description="版本号")
    tags: list[str] = Field(description="标签列表")


class ToolListResponse(BaseModel):
    """工具列表响应"""

    items: list[ToolResponse] = Field(description="工具列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
