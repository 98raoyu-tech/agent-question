"""
KV 记忆存储模块

本模块实现了基于 Redis 的高速上下文缓存，支持键值对存储和批量操作。
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as redis

from .base import MemoryEntry, MemoryStore

logger = logging.getLogger(__name__)


class KVMemoryStore(MemoryStore):
    """
    基于 Redis 的 KV 记忆存储

    使用 Redis 实现高速键值对存储，支持 TTL 过期和批量操作。

    Attributes:
        client: Redis 异步客户端
        default_ttl: 默认过期时间（秒）
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: Optional[int] = 3600,
        key_prefix: str = "memory:",
    ):
        """
        初始化 KV 记忆存储

        Args:
            redis_url: Redis 连接 URL
            default_ttl: 默认过期时间（秒），None 表示永不过期
            key_prefix: 键前缀
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """
        初始化 Redis 连接

        创建 Redis 客户端并验证连接状态。
        """
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )

            # 验证连接
            await self.client.ping()

            logger.info("KV 记忆存储初始化完成")

        except Exception as e:
            logger.error(f"KV 记忆存储初始化失败: {e}")
            raise

    def _get_full_key(self, key: str) -> str:
        """
        获取完整的 Redis 键

        Args:
            key: 原始键

        Returns:
            添加前缀后的完整键
        """
        return f"{self.key_prefix}{key}"

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """
        存储键值对

        Args:
            key: 键
            value: 值
            metadata: 可选的元数据信息
            ttl: 可选的过期时间（秒）
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_key = self._get_full_key(key)

            # 创建记忆条目
            entry = MemoryEntry(
                key=key,
                value=value,
                metadata=metadata or {},
            )

            # 序列化为 JSON
            data = json.dumps(entry.to_dict())

            # 设置过期时间
            expiry = ttl or self.default_ttl

            if expiry:
                await self.client.setex(full_key, expiry, data)
            else:
                await self.client.set(full_key, data)

            logger.debug(f"KV 记忆已存储: {key}")

        except Exception as e:
            logger.error(f"存储 KV 记忆失败 [{key}]: {e}")
            raise

    async def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """
        检索记忆条目

        Args:
            key: 要检索的键

        Returns:
            MemoryEntry 实例，如果不存在则返回 None
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_key = self._get_full_key(key)
            data = await self.client.get(full_key)

            if not data:
                return None

            # 反序列化
            entry_dict = json.loads(data)
            return MemoryEntry.from_dict(entry_dict)

        except Exception as e:
            logger.error(f"检索 KV 记忆失败 [{key}]: {e}")
            raise

    async def search(self, query: str, top_k: int = 10) -> list[MemoryEntry]:
        """
        搜索记忆条目（基于键模式匹配）

        Args:
            query: 搜索查询字符串（支持通配符）
            top_k: 返回的最大结果数量

        Returns:
            匹配的记忆条目列表
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            pattern = f"{self.key_prefix}*{query}*"
            keys = []
            async for key in self.client.scan_iter(match=pattern, count=top_k):
                keys.append(key)
                if len(keys) >= top_k:
                    break

            entries = []
            for full_key in keys:
                data = await self.client.get(full_key)
                if data:
                    entry_dict = json.loads(data)
                    entries.append(MemoryEntry.from_dict(entry_dict))

            return entries

        except Exception as e:
            logger.error(f"KV 记忆搜索失败: {e}")
            raise

    async def batch_store(self, entries: list[MemoryEntry]) -> None:
        """
        批量存储记忆条目

        Args:
            entries: 记忆条目列表
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            pipeline = self.client.pipeline()

            for entry in entries:
                full_key = self._get_full_key(entry.key)
                data = json.dumps(entry.to_dict())
                expiry = entry.ttl or self.default_ttl

                if expiry:
                    pipeline.setex(full_key, expiry, data)
                else:
                    pipeline.set(full_key, data)

            await pipeline.execute()

            logger.debug(f"批量存储 KV 记忆完成，数量: {len(entries)}")

        except Exception as e:
            logger.error(f"批量存储 KV 记忆失败: {e}")
            raise

    async def batch_retrieve(self, keys: list[str]) -> list[MemoryEntry]:
        """
        批量检索记忆条目

        Args:
            keys: 要检索的键列表

        Returns:
            MemoryEntry 列表
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_keys = [self._get_full_key(key) for key in keys]
            pipeline = self.client.pipeline()

            for full_key in full_keys:
                pipeline.get(full_key)

            results = await pipeline.execute()

            entries = []
            for data in results:
                if data:
                    entry_dict = json.loads(data)
                    entries.append(MemoryEntry.from_dict(entry_dict))

            return entries

        except Exception as e:
            logger.error(f"批量检索 KV 记忆失败: {e}")
            raise

    async def exists(self, key: str) -> bool:
        """
        判断键是否存在

        Args:
            key: 要检查的键

        Returns:
            键是否存在
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_key = self._get_full_key(key)
            return bool(await self.client.exists(full_key))

        except Exception as e:
            logger.error(f"检查 KV 记忆存在失败 [{key}]: {e}")
            raise

    async def delete(self, key: str) -> None:
        """
        删除记忆条目

        Args:
            key: 要删除的键
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_key = self._get_full_key(key)
            await self.client.delete(full_key)

            logger.debug(f"KV 记忆已删除: {key}")

        except Exception as e:
            logger.error(f"删除 KV 记忆失败 [{key}]: {e}")
            raise

    async def clear(self, pattern: str = "*") -> None:
        """
        清空记忆条目

        Args:
            pattern: 键匹配模式，默认为所有键
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_pattern = f"{self.key_prefix}{pattern}"
            keys = []

            async for key in self.client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                await self.client.delete(*keys)
                logger.info(f"KV 记忆已清空，删除 {len(keys)} 个键")
            else:
                logger.info("KV 记忆为空")

        except Exception as e:
            logger.error(f"清空 KV 记忆失败: {e}")
            raise

    async def set_ttl(self, key: str, ttl: int) -> None:
        """
        设置键的过期时间

        Args:
            key: 键
            ttl: 过期时间（秒）
        """
        if not self.client:
            raise RuntimeError("KV 记忆存储未初始化，请先调用 initialize()")

        try:
            full_key = self._get_full_key(key)
            await self.client.expire(full_key, ttl)

            logger.debug(f"KV 记忆 TTL 已设置: {key} -> {ttl}s")

        except Exception as e:
            logger.error(f"设置 KV 记忆 TTL 失败 [{key}]: {e}")
            raise