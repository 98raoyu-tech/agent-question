"""
图记忆存储模块

本模块实现了基于 Neo4j 的实体关系记忆存储，支持图结构数据的存储和查询。
"""

import json
import logging
from typing import Any, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from .base import MemoryEntry, MemoryStore

logger = logging.getLogger(__name__)


class GraphMemoryStore(MemoryStore):
    """
    基于 Neo4j 的图记忆存储

    使用 Neo4j 图数据库存储实体和关系，支持复杂的图遍历和关系查询。

    Attributes:
        driver: Neo4j 异步驱动实例
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ):
        """
        初始化图记忆存储

        Args:
            uri: Neo4j 数据库连接 URI
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver: Optional[AsyncDriver] = None

    async def initialize(self) -> None:
        """
        初始化 Neo4j 连接

        创建数据库连接并验证连接状态。
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )

            # 验证连接
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as test")
                await result.single()

            logger.info("图记忆存储初始化完成")

        except Exception as e:
            logger.error(f"图记忆存储初始化失败: {e}")
            raise

    async def store(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """
        存储记忆条目（作为实体）

        Args:
            key: 记忆条目的唯一标识符
            value: 要存储的值
            metadata: 可选的元数据信息
        """
        await self.store_entity("Memory", key, {
            "value": json.dumps(value) if not isinstance(value, str) else value,
            "metadata": json.dumps(metadata or {}),
        })

    async def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """
        检索记忆条目

        Args:
            key: 要检索的记忆条目标识符

        Returns:
            MemoryEntry 实例，如果不存在则返回 None
        """
        result = await self.query_entity(key)
        if not result:
            return None

        properties = result.get("properties", {})
        return MemoryEntry(
            key=key,
            value=json.loads(properties.get("value", "null")),
            metadata=json.loads(properties.get("metadata", "{}")),
            created_at=properties.get("created_at"),
            updated_at=properties.get("updated_at"),
        )

    async def search(self, query: str, top_k: int = 10) -> list[MemoryEntry]:
        """
        基于图结构的搜索

        Args:
            query: 搜索查询字符串
            top_k: 返回的最大结果数量

        Returns:
            匹配的记忆条目列表
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (n:Memory)
                    WHERE n.value CONTAINS $query
                    RETURN n
                    LIMIT $limit
                    """,
                    query=query,
                    limit=top_k,
                )

                entries = []
                async for record in result:
                    node = record["n"]
                    properties = dict(node)
                    entries.append(MemoryEntry(
                        key=properties.get("entity_id", ""),
                        value=json.loads(properties.get("value", "null")),
                        metadata=json.loads(properties.get("metadata", "{}")),
                        created_at=properties.get("created_at"),
                        updated_at=properties.get("updated_at"),
                    ))

                return entries

        except Exception as e:
            logger.error(f"图记忆搜索失败: {e}")
            raise

    async def store_entity(
        self,
        entity_type: str,
        entity_id: str,
        properties: dict,
    ) -> None:
        """
        存储实体

        Args:
            entity_type: 实体类型（标签）
            entity_id: 实体唯一标识符
            properties: 实体属性
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    f"""
                    MERGE (n:{entity_type} {{entity_id: $entity_id}})
                    SET n += $properties
                    SET n.updated_at = datetime()
                    """,
                    entity_id=entity_id,
                    properties=properties,
                )

            logger.debug(f"实体已存储: {entity_type}/{entity_id}")

        except Exception as e:
            logger.error(f"存储实体失败 [{entity_type}/{entity_id}]: {e}")
            raise

    async def store_relation(
        self,
        source_id: str,
        relation: str,
        target_id: str,
        properties: Optional[dict] = None,
    ) -> None:
        """
        存储关系

        Args:
            source_id: 源实体 ID
            relation: 关系类型
            target_id: 目标实体 ID
            properties: 关系属性
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    f"""
                    MATCH (a {{entity_id: $source_id}})
                    MATCH (b {{entity_id: $target_id}})
                    MERGE (a)-[r:{relation}]->(b)
                    SET r += $properties
                    SET r.updated_at = datetime()
                    """,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties or {},
                )

            logger.debug(f"关系已存储: {source_id} -[{relation}]-> {target_id}")

        except Exception as e:
            logger.error(f"存储关系失败: {e}")
            raise

    async def query_entity(self, entity_id: str) -> Optional[dict]:
        """
        查询实体及其关系

        Args:
            entity_id: 实体唯一标识符

        Returns:
            包含实体信息和关系的字典，如果不存在则返回 None
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (n {entity_id: $entity_id})
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, collect({
                        relation: type(r),
                        target_id: m.entity_id,
                        properties: properties(r)
                    }) as relations
                    """,
                    entity_id=entity_id,
                )

                record = await result.single()
                if not record:
                    return None

                node = record["n"]
                relations = record["relations"]

                return {
                    "entity_id": entity_id,
                    "properties": dict(node),
                    "relations": relations,
                }

        except Exception as e:
            logger.error(f"查询实体失败 [{entity_id}]: {e}")
            raise

    async def query_relations(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
    ) -> list[dict]:
        """
        查询实体的特定关系

        Args:
            entity_id: 实体唯一标识符
            relation_type: 可选的关系类型过滤

        Returns:
            关系列表
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                if relation_type:
                    result = await session.run(
                        f"""
                        MATCH (n {{entity_id: $entity_id}})-[r:{relation_type}]->(m)
                        RETURN type(r) as relation, m.entity_id as target_id, properties(r) as properties
                        """,
                        entity_id=entity_id,
                    )
                else:
                    result = await session.run(
                        """
                        MATCH (n {entity_id: $entity_id})-[r]->(m)
                        RETURN type(r) as relation, m.entity_id as target_id, properties(r) as properties
                        """,
                        entity_id=entity_id,
                    )

                relations = []
                async for record in result:
                    relations.append({
                        "relation": record["relation"],
                        "target_id": record["target_id"],
                        "properties": record["properties"],
                    })

                return relations

        except Exception as e:
            logger.error(f"查询关系失败 [{entity_id}]: {e}")
            raise

    async def traverse_graph(
        self,
        start_id: str,
        max_depth: int = 3,
    ) -> dict:
        """
        图遍历

        从指定实体开始遍历图结构，返回指定深度内的所有节点和关系。

        Args:
            start_id: 起始实体 ID
            max_depth: 最大遍历深度

        Returns:
            包含遍历结果的字典
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH path = (start {entity_id: $start_id})-[*1..$max_depth]-(end)
                    RETURN nodes(path) as nodes, relationships(path) as relationships
                    """,
                    start_id=start_id,
                    max_depth=max_depth,
                )

                nodes = set()
                relationships = []

                async for record in result:
                    for node in record["nodes"]:
                        nodes.add(node.get("entity_id"))
                    for rel in record["relationships"]:
                        relationships.append({
                            "start": rel.start_node.get("entity_id"),
                            "end": rel.end_node.get("entity_id"),
                            "type": rel.type,
                            "properties": dict(rel),
                        })

                return {
                    "start_id": start_id,
                    "nodes": list(nodes),
                    "relationships": relationships,
                }

        except Exception as e:
            logger.error(f"图遍历失败 [{start_id}]: {e}")
            raise

    async def delete(self, key: str) -> None:
        """
        删除实体

        Args:
            key: 要删除的实体标识符
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    """
                    MATCH (n {entity_id: $entity_id})
                    DETACH DELETE n
                    """,
                    entity_id=key,
                )

            logger.debug(f"实体已删除: {key}")

        except Exception as e:
            logger.error(f"删除实体失败 [{key}]: {e}")
            raise

    async def clear(self) -> None:
        """
        清空所有实体和关系
        """
        if not self.driver:
            raise RuntimeError("图记忆存储未初始化，请先调用 initialize()")

        try:
            async with self.driver.session(database=self.database) as session:
                await session.run("MATCH (n) DETACH DELETE n")

            logger.info("图记忆存储已清空")

        except Exception as e:
            logger.error(f"清空图记忆存储失败: {e}")
            raise