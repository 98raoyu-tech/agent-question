"""
向量记忆存储模块

本模块实现了基于 pgvector 的语义记忆存储，支持向量嵌入和相似度搜索。
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

import asyncpg
import numpy as np

from .base import MemoryEntry, MemoryStore

logger = logging.getLogger(__name__)


class VectorMemoryStore(MemoryStore):
    """
    基于 pgvector 的向量记忆存储

    使用 PostgreSQL 的 pgvector 扩展实现语义相似度搜索。
    支持文本向量化、存储和基于余弦相似度的检索。

    Attributes:
        connection: asyncpg 数据库连接
        embedding_model: 向量嵌入模型名称
        table_name: 存储表名
        dimension: 向量维度
    """

    def __init__(
        self,
        database_url: str,
        embedding_model: str = "text-embedding-ada-002",
        table_name: str = "vector_memories",
        dimension: int = 1536,
    ):
        """
        初始化向量记忆存储

        Args:
            database_url: PostgreSQL 数据库连接 URL
            embedding_model: 向量嵌入模型名称
            table_name: 存储表名
            dimension: 向量维度
        """
        self.database_url = database_url
        self.embedding_model = embedding_model
        self.table_name = table_name
        self.dimension = dimension
        self.connection: Optional[asyncpg.Connection] = None

    async def initialize(self) -> None:
        """
        初始化数据库连接和表结构

        创建必要的表和索引，启用 pgvector 扩展。
        """
        try:
            self.connection = await asyncpg.connect(self.database_url)

            # 启用 pgvector 扩展
            await self.connection.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # 创建记忆表
            await self.connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key VARCHAR(255) PRIMARY KEY,
                    value TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    embedding vector({self.dimension}),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ttl INTEGER
                )
            """)

            # 创建向量索引以加速相似度搜索
            await self.connection.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding
                ON {self.table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)

            logger.info(f"向量记忆存储初始化完成，表名: {self.table_name}")

        except Exception as e:
            logger.error(f"向量记忆存储初始化失败: {e}")
            raise

    async def store(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """
        存储记忆条目及其向量嵌入

        Args:
            key: 记忆条目的唯一标识符
            value: 要存储的值（文本）
            metadata: 可选的元数据信息
        """
        if not self.connection:
            raise RuntimeError("向量记忆存储未初始化，请先调用 initialize()")

        try:
            # 生成向量嵌入
            embedding = await self._generate_embedding(str(value))
            embedding_str = f"[{','.join(map(str, embedding))}]"

            # 存储到数据库
            await self.connection.execute(
                f"""
                INSERT INTO {self.table_name} (key, value, metadata, embedding, created_at, updated_at)
                VALUES ($1, $2, $3, $4::vector, NOW(), NOW())
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                key,
                str(value),
                json.dumps(metadata or {}),
                embedding_str,
            )

            logger.debug(f"记忆条目已存储: {key}")

        except Exception as e:
            logger.error(f"存储记忆条目失败 [{key}]: {e}")
            raise

    async def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """
        按 key 检索记忆条目

        Args:
            key: 要检索的记忆条目标识符

        Returns:
            MemoryEntry 实例，如果不存在则返回 None
        """
        if not self.connection:
            raise RuntimeError("向量记忆存储未初始化，请先调用 initialize()")

        try:
            row = await self.connection.fetchrow(
                f"""
                SELECT key, value, metadata, created_at, updated_at, ttl
                FROM {self.table_name}
                WHERE key = $1
                """,
                key,
            )

            if not row:
                return None

            return MemoryEntry(
                key=row["key"],
                value=row["value"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                ttl=row["ttl"],
            )

        except Exception as e:
            logger.error(f"检索记忆条目失败 [{key}]: {e}")
            raise

    async def search(self, query: str, top_k: int = 10) -> list[MemoryEntry]:
        """
        搜索记忆条目（基于文本匹配）

        Args:
            query: 搜索查询字符串
            top_k: 返回的最大结果数量

        Returns:
            匹配的记忆条目列表
        """
        return await self.semantic_search(query, top_k)

    async def semantic_search(
        self, query_text: str, top_k: int = 10, threshold: float = 0.7
    ) -> list[MemoryEntry]:
        """
        语义相似度搜索

        基于向量嵌入的余弦相似度进行语义搜索。

        Args:
            query_text: 查询文本
            top_k: 返回的最大结果数量
            threshold: 相似度阈值（0-1）

        Returns:
            按相似度排序的记忆条目列表
        """
        if not self.connection:
            raise RuntimeError("向量记忆存储未初始化，请先调用 initialize()")

        try:
            # 生成查询向量
            query_embedding = await self._generate_embedding(query_text)
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # 执行相似度搜索
            rows = await self.connection.fetch(
                f"""
                SELECT key, value, metadata, created_at, updated_at, ttl,
                       1 - (embedding <=> $1::vector) as similarity
                FROM {self.table_name}
                WHERE 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                query_embedding_str,
                threshold,
                top_k,
            )

            results = []
            for row in rows:
                entry = MemoryEntry(
                    key=row["key"],
                    value=row["value"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    ttl=row["ttl"],
                )
                # 将相似度信息添加到元数据中
                entry.metadata["similarity"] = row["similarity"]
                results.append(entry)

            logger.debug(f"语义搜索完成，查询: {query_text[:50]}...，结果数量: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            raise

    async def delete(self, key: str) -> None:
        """
        删除记忆条目

        Args:
            key: 要删除的记忆条目标识符
        """
        if not self.connection:
            raise RuntimeError("向量记忆存储未初始化，请先调用 initialize()")

        try:
            result = await self.connection.execute(
                f"DELETE FROM {self.table_name} WHERE key = $1", key
            )
            logger.debug(f"记忆条目已删除: {key}, 结果: {result}")

        except Exception as e:
            logger.error(f"删除记忆条目失败 [{key}]: {e}")
            raise

    async def clear(self) -> None:
        """
        清空所有记忆条目
        """
        if not self.connection:
            raise RuntimeError("向量记忆存储未初始化，请先调用 initialize()")

        try:
            await self.connection.execute(f"TRUNCATE TABLE {self.table_name}")
            logger.info("向量记忆存储已清空")

        except Exception as e:
            logger.error(f"清空向量记忆存储失败: {e}")
            raise

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        生成文本的向量嵌入

        使用配置的嵌入模型生成文本的向量表示。

        Args:
            text: 要嵌入的文本

        Returns:
            向量嵌入列表
        """
        # 注意：这里需要根据实际使用的嵌入模型实现
        # 示例使用随机向量，实际应调用 OpenAI 或其他嵌入 API
        # TODO: 集成实际的嵌入模型
        logger.warning("使用随机向量作为嵌入，请集成实际的嵌入模型")
        return list(np.random.randn(self.dimension))

    @staticmethod
    async def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            a: 第一个向量
            b: 第二个向量

        Returns:
            余弦相似度值（-1 到 1）
        """
        a_array = np.array(a)
        b_array = np.array(b)
        return float(np.dot(a_array, b_array) / (np.linalg.norm(a_array) * np.linalg.norm(b_array)))