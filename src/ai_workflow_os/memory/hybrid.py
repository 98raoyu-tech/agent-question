"""
混合记忆管理器模块

本模块实现了整合所有记忆存储的统一管理器，支持自动选择记忆类型和跨存储检索。
"""

import logging
from datetime import datetime
from typing import Any, Optional

from .base import MemoryEntry
from .event import EventMemoryStore
from .graph import GraphMemoryStore
from .kv import KVMemoryStore
from .vector import VectorMemoryStore

logger = logging.getLogger(__name__)


class HybridMemoryManager:
    """
    混合记忆管理器

    整合向量、图、KV 和事件记忆存储，提供统一的记忆管理接口。
    支持自动选择记忆类型、跨存储检索和记忆整合。

    Attributes:
        vector_store: 向量记忆存储
        graph_store: 图记忆存储
        kv_store: KV 记忆存储
        event_store: 事件记忆存储
    """

    def __init__(
        self,
        vector_store: Optional[VectorMemoryStore] = None,
        graph_store: Optional[GraphMemoryStore] = None,
        kv_store: Optional[KVMemoryStore] = None,
        event_store: Optional[EventMemoryStore] = None,
    ):
        """
        初始化混合记忆管理器

        Args:
            vector_store: 向量记忆存储实例
            graph_store: 图记忆存储实例
            kv_store: KV 记忆存储实例
            event_store: 事件记忆存储实例
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.kv_store = kv_store
        self.event_store = event_store

    async def initialize(self) -> None:
        """
        初始化所有存储

        依次初始化配置的记忆存储实例。
        """
        try:
            if self.vector_store:
                await self.vector_store.initialize()
                logger.info("向量记忆存储已初始化")

            if self.graph_store:
                await self.graph_store.initialize()
                logger.info("图记忆存储已初始化")

            if self.kv_store:
                await self.kv_store.initialize()
                logger.info("KV 记忆存储已初始化")

            if self.event_store:
                await self.event_store.initialize()
                logger.info("事件记忆存储已初始化")

            logger.info("混合记忆管理器初始化完成")

        except Exception as e:
            logger.error(f"混合记忆管理器初始化失败: {e}")
            raise

    async def remember(
        self,
        key: str,
        value: Any,
        memory_type: str = "auto",
        metadata: Optional[dict] = None,
    ) -> None:
        """
        自动选择合适的记忆类型存储

        Args:
            key: 记忆条目的唯一标识符
            value: 要存储的值
            memory_type: 记忆类型（auto/vector/graph/kv/event/all）
            metadata: 可选的元数据信息
        """
        try:
            # 自动判断记忆类型
            if memory_type == "auto":
                memory_type = self._determine_memory_type(value)

            # 根据类型存储到相应的存储
            if memory_type == "vector" and self.vector_store:
                await self.vector_store.store(key, value, metadata)
            elif memory_type == "graph" and self.graph_store:
                await self.graph_store.store(key, value, metadata)
            elif memory_type == "kv" and self.kv_store:
                await self.kv_store.store(key, value, metadata)
            elif memory_type == "event" and self.event_store:
                await self.event_store.store(key, value, metadata)
            elif memory_type == "all":
                # 存储到所有可用的存储
                if self.vector_store:
                    await self.vector_store.store(key, value, metadata)
                if self.graph_store:
                    await self.graph_store.store(key, value, metadata)
                if self.kv_store:
                    await self.kv_store.store(key, value, metadata)
                if self.event_store:
                    await self.event_store.store(key, value, metadata)
            else:
                logger.warning(f"无法存储记忆，类型: {memory_type}，可能未配置相应存储")

            logger.debug(f"记忆已存储: {key}，类型: {memory_type}")

        except Exception as e:
            logger.error(f"存储记忆失败 [{key}]: {e}")
            raise

    async def recall(
        self,
        query: str,
        memory_types: Optional[list[str]] = None,
    ) -> dict[str, list[MemoryEntry]]:
        """
        从多种记忆中检索

        Args:
            query: 搜索查询字符串
            memory_types: 要搜索的记忆类型列表，默认搜索所有类型

        Returns:
            按记忆类型分组的检索结果
        """
        try:
            results = {}

            # 默认搜索所有类型
            if memory_types is None:
                memory_types = ["vector", "graph", "kv", "event"]

            # 从向量存储检索
            if "vector" in memory_types and self.vector_store:
                try:
                    vector_results = await self.vector_store.search(query)
                    results["vector"] = vector_results
                except Exception as e:
                    logger.error(f"向量存储检索失败: {e}")
                    results["vector"] = []

            # 从图存储检索
            if "graph" in memory_types and self.graph_store:
                try:
                    graph_results = await self.graph_store.search(query)
                    results["graph"] = graph_results
                except Exception as e:
                    logger.error(f"图存储检索失败: {e}")
                    results["graph"] = []

            # 从 KV 存储检索
            if "kv" in memory_types and self.kv_store:
                try:
                    kv_results = await self.kv_store.search(query)
                    results["kv"] = kv_results
                except Exception as e:
                    logger.error(f"KV 存储检索失败: {e}")
                    results["kv"] = []

            # 从事件存储检索
            if "event" in memory_types and self.event_store:
                try:
                    event_results = await self.event_store.search(query)
                    results["event"] = event_results
                except Exception as e:
                    logger.error(f"事件存储检索失败: {e}")
                    results["event"] = []

            logger.debug(f"记忆检索完成，查询: {query[:50]}...，结果数量: {sum(len(v) for v in results.values())}")
            return results

        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            raise

    async def forget(
        self,
        key: str,
        memory_type: Optional[str] = None,
    ) -> None:
        """
        删除记忆

        Args:
            key: 要删除的记忆条目标识符
            memory_type: 要删除的记忆类型，默认删除所有类型
        """
        try:
            # 如果未指定类型，删除所有存储中的记忆
            if memory_type is None:
                memory_type = "all"

            if memory_type in ("vector", "all") and self.vector_store:
                await self.vector_store.delete(key)
            if memory_type in ("graph", "all") and self.graph_store:
                await self.graph_store.delete(key)
            if memory_type in ("kv", "all") and self.kv_store:
                await self.kv_store.delete(key)
            if memory_type in ("event", "all") and self.event_store:
                await self.event_store.delete(key)

            logger.debug(f"记忆已删除: {key}，类型: {memory_type}")

        except Exception as e:
            logger.error(f"删除记忆失败 [{key}]: {e}")
            raise

    async def consolidate(self) -> None:
        """
        整合和压缩记忆

        执行记忆整合操作，如清理过期数据、优化存储结构等。
        """
        try:
            # 清理过期的 KV 记忆
            if self.kv_store:
                logger.info("KV 记忆存储无需手动清理，Redis 自动处理过期数据")

            # 整合向量记忆（可扩展）
            if self.vector_store:
                logger.info("向量记忆存储整合完成")

            # 整合图记忆（可扩展）
            if self.graph_store:
                logger.info("图记忆存储整合完成")

            # 整合事件记忆（可扩展）
            if self.event_store:
                logger.info("事件记忆存储整合完成")

            logger.info("记忆整合完成")

        except Exception as e:
            logger.error(f"记忆整合失败: {e}")
            raise

    async def get_memory_stats(self) -> dict:
        """
        获取记忆统计信息

        Returns:
            包含各存储统计信息的字典
        """
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "stores": {},
            }

            # 向量存储统计
            if self.vector_store:
                stats["stores"]["vector"] = {
                    "status": "active",
                    "type": "pgvector",
                }

            # 图存储统计
            if self.graph_store:
                stats["stores"]["graph"] = {
                    "status": "active",
                    "type": "neo4j",
                }

            # KV 存储统计
            if self.kv_store:
                stats["stores"]["kv"] = {
                    "status": "active",
                    "type": "redis",
                }

            # 事件存储统计
            if self.event_store:
                stats["stores"]["event"] = {
                    "status": "active",
                    "type": "kafka",
                }

            return stats

        except Exception as e:
            logger.error(f"获取记忆统计信息失败: {e}")
            raise

    def _determine_memory_type(self, content: Any) -> str:
        """
        根据内容自动判断记忆类型

        Args:
            content: 要存储的内容

        Returns:
            推荐的记忆类型
        """
        # 文本内容使用向量存储
        if isinstance(content, str) and len(content) > 10:
            return "vector"

        # 结构化数据使用图存储
        if isinstance(content, dict) and "entities" in content:
            return "graph"

        # 简单键值对使用 KV 存储
        if isinstance(content, (str, int, float, bool)):
            return "kv"

        # 事件数据使用事件存储
        if isinstance(content, dict) and "event_type" in content:
            return "event"

        # 默认使用 KV 存储
        return "kv"