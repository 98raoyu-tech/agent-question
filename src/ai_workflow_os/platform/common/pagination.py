"""
分页查询参数和响应

提供统一的分页请求参数和响应结构，支持游标分页和偏移量分页。
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedRequest(BaseModel):
    """分页请求参数

    Attributes:
        page: 页码，从1开始
        page_size: 每页大小，默认20，最大100
        sort_by: 排序字段
        sort_order: 排序方向（asc/desc）
        search: 搜索关键词
    """

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")
    search: Optional[str] = Field(default=None, description="搜索关键词")

    @property
    def offset(self) -> int:
        """计算偏移量

        Returns:
            数据偏移量
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """计算限制数量

        Returns:
            数据限制数量
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应结果

    Attributes:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        total_pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页
    """

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, ge=0, description="总记录数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=20, ge=1, description="每页大小")
    total_pages: int = Field(default=0, ge=0, description="总页数")
    has_next: bool = Field(default=False, description="是否有下一页")
    has_prev: bool = Field(default=False, description="是否有上一页")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """创建分页响应实例

        Args:
            items: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页大小

        Returns:
            分页响应实例
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
