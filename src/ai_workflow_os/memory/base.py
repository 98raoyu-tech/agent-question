"""
记忆存储基类模块

本模块定义了记忆存储的抽象基类和记忆条目数据类，为所有记忆存储实现提供统一接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryEntry:
    """
    记忆条目数据类

    表示一个完整的记忆条目，包含键值对、元数据和时间信息。

    Attributes:
        key: 记忆条目的唯一标识符
        value: 记忆条目的值，可以是任意类型
        metadata: 附加的元数据信息
        created_at: 创建时间
        updated_at: 最后更新时间
        ttl: 可选的生存时间（秒），None表示永不过期
    """

    key: str
    value: Any
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None

    def to_dict(self) -> dict:
        """
        将记忆条目转换为字典格式

        Returns:
            包含所有字段的字典
        """
        return {
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """
        从字典创建记忆条目

        Args:
            data: 包含记忆条目数据的字典

        Returns:
            MemoryEntry 实例
        """
        return cls(
            key=data["key"],
            value=data["value"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            ttl=data.get("ttl"),
        )


class MemoryStore(ABC):
    """
    记忆存储抽象基类

    定义了所有记忆存储实现必须提供的核心接口。
    所有方法都是异步的，以支持高并发操作。
    """

    @abstractmethod
    async def store(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """
        存储记忆条目

        Args:
            key: 记忆条目的唯一标识符
            value: 要存储的值
            metadata: 可选的元数据信息
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """
        检索记忆条目

        Args:
            key: 要检索的记忆条目标识符

        Returns:
            记忆条目的值，如果不存在则返回 None
        """
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> list:
        """
        搜索记忆条目

        Args:
            query: 搜索查询字符串
            top_k: 返回的最大结果数量

        Returns:
            匹配的记忆条目列表
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        删除记忆条目

        Args:
            key: 要删除的记忆条目标识符
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        清空所有记忆条目
        """
        pass