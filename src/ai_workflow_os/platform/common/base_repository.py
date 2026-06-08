"""
仓储抽象基类

定义数据访问层的通用接口，支持CRUD操作、分页查询和多租户隔离。
"""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from .base_entity import BaseEntity
from .pagination import PaginatedRequest, PaginatedResponse

T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """仓储抽象基类

    所有仓储实现必须继承此类，提供统一的数据访问接口。

    Type Parameters:
        T: 实体类型，必须继承BaseEntity
    """

    @abstractmethod
    async def find_by_id(self, entity_id: str, tenant_id: Optional[str] = None) -> Optional[T]:
        """根据ID查找实体

        Args:
            entity_id: 实体唯一标识
            tenant_id: 租户标识，用于多租户隔离

        Returns:
            实体实例，未找到返回None
        """
        ...

    @abstractmethod
    async def find_all(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[T]:
        """分页查询实体列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        ...

    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体（创建或更新）

        Args:
            entity: 待保存的实体

        Returns:
            保存后的实体
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: str, tenant_id: Optional[str] = None) -> bool:
        """删除实体（软删除）

        Args:
            entity_id: 实体唯一标识
            tenant_id: 租户标识

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def exists(self, entity_id: str, tenant_id: Optional[str] = None) -> bool:
        """检查实体是否存在

        Args:
            entity_id: 实体唯一标识
            tenant_id: 租户标识

        Returns:
            是否存在
        """
        ...

    @abstractmethod
    async def count(self, tenant_id: Optional[str] = None, filters: Optional[dict] = None) -> int:
        """统计实体数量

        Args:
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            实体数量
        """
        ...
