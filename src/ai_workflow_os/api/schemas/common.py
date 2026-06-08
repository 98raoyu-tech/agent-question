"""
通用Schema定义

提供统一的API响应格式、分页响应和错误响应模型。
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""

    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "success") -> "APIResponse[T]":
        """创建成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 500, message: str = "服务器内部错误") -> "APIResponse[None]":
        """创建错误响应"""
        return cls(code=code, message=message, data=None)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")

    @property
    def total_pages(self) -> int:
        """计算总页数"""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1


class ErrorResponse(BaseModel):
    """错误响应格式"""

    code: int = Field(description="错误状态码")
    message: str = Field(description="错误消息")
    detail: Optional[str] = Field(default=None, description="错误详情")
