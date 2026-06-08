"""
工作流引擎仓储实现

提供工作流定义、节点、边和执行记录的内存存储实现。
"""

import logging

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.workflow_definition import WorkflowDefinition
from ..domain.workflow_edge import WorkflowEdge
from ..domain.workflow_execution import WorkflowExecution
from ..domain.workflow_node import WorkflowNode

logger = logging.getLogger(__name__)


class WorkflowRepository:
    """工作流引擎仓储实现

    基于内存字典的仓储实现，管理工作流定义、节点、边和执行记录。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._nodes: dict[str, WorkflowNode] = {}
        self._edges: dict[str, WorkflowEdge] = {}
        self._executions: dict[str, WorkflowExecution] = {}

    # =========================================================================
    # 工作流定义操作
    # =========================================================================

    async def save_workflow(self, entity: WorkflowDefinition) -> WorkflowDefinition:
        """保存工作流定义

        Args:
            entity: 工作流定义实体

        Returns:
            保存后的工作流定义
        """
        self._workflows[entity.id] = entity
        logger.debug("工作流定义已保存: id=%s, name=%s", entity.id, entity.name)
        return entity

    async def find_workflow_by_id(
        self,
        entity_id: str,
        tenant_id: str | None = None,
    ) -> WorkflowDefinition | None:
        """根据ID查找工作流定义

        Args:
            entity_id: 工作流标识
            tenant_id: 租户标识

        Returns:
            工作流定义实体，未找到返回None
        """
        workflow = self._workflows.get(entity_id)
        if workflow is not None and tenant_id is not None and workflow.tenant_id != tenant_id:
            return None
        if workflow is not None and workflow.is_deleted:
            return None
        return workflow

    async def find_all_workflows(
        self,
        pagination: PaginatedRequest,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[WorkflowDefinition]:
        """分页查询工作流定义列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        items = [w for w in self._workflows.values() if not w.is_deleted]

        if tenant_id is not None:
            items = [w for w in items if w.tenant_id == tenant_id]

        items.sort(key=lambda w: w.created_at, reverse=True)
        total = len(items)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = items[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # =========================================================================
    # 节点操作
    # =========================================================================

    async def save_node(self, entity: WorkflowNode) -> WorkflowNode:
        """保存节点

        Args:
            entity: 节点实体

        Returns:
            保存后的节点
        """
        self._nodes[entity.id] = entity
        logger.debug("节点已保存: id=%s, name=%s", entity.id, entity.name)
        return entity

    async def save_nodes(self, entities: list[WorkflowNode]) -> list[WorkflowNode]:
        """批量保存节点

        Args:
            entities: 节点列表

        Returns:
            保存后的节点列表
        """
        for entity in entities:
            self._nodes[entity.id] = entity
        logger.debug("批量保存节点: count=%d", len(entities))
        return entities

    async def find_node_by_id(self, entity_id: str) -> WorkflowNode | None:
        """根据ID查找节点

        Args:
            entity_id: 节点标识

        Returns:
            节点实体，未找到返回None
        """
        return self._nodes.get(entity_id)

    async def find_nodes_by_workflow_id(self, workflow_id: str) -> list[WorkflowNode]:
        """根据工作流标识查找节点列表

        Args:
            workflow_id: 工作流标识

        Returns:
            节点列表
        """
        return [n for n in self._nodes.values() if n.workflow_id == workflow_id and not n.is_deleted]

    # =========================================================================
    # 边操作
    # =========================================================================

    async def save_edge(self, entity: WorkflowEdge) -> WorkflowEdge:
        """保存边

        Args:
            entity: 边实体

        Returns:
            保存后的边
        """
        self._edges[entity.id] = entity
        logger.debug("边已保存: id=%s", entity.id)
        return entity

    async def save_edges(self, entities: list[WorkflowEdge]) -> list[WorkflowEdge]:
        """批量保存边

        Args:
            entities: 边列表

        Returns:
            保存后的边列表
        """
        for entity in entities:
            self._edges[entity.id] = entity
        logger.debug("批量保存边: count=%d", len(entities))
        return entities

    async def find_edges_by_workflow_id(self, workflow_id: str) -> list[WorkflowEdge]:
        """根据工作流标识查找边列表

        Args:
            workflow_id: 工作流标识

        Returns:
            边列表
        """
        return [e for e in self._edges.values() if e.workflow_id == workflow_id and not e.is_deleted]

    # =========================================================================
    # 执行记录操作
    # =========================================================================

    async def save_execution(self, entity: WorkflowExecution) -> WorkflowExecution:
        """保存执行记录

        Args:
            entity: 执行记录实体

        Returns:
            保存后的执行记录
        """
        self._executions[entity.id] = entity
        logger.debug("执行记录已保存: id=%s, workflow_id=%s", entity.id, entity.workflow_id)
        return entity

    async def find_execution_by_id(self, entity_id: str) -> WorkflowExecution | None:
        """根据ID查找执行记录

        Args:
            entity_id: 执行记录标识

        Returns:
            执行记录实体，未找到返回None
        """
        return self._executions.get(entity_id)

    async def find_executions_by_workflow_id(
        self,
        workflow_id: str,
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[WorkflowExecution]:
        """根据工作流标识分页查询执行记录

        Args:
            workflow_id: 工作流标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        items = [
            ex for ex in self._executions.values()
            if ex.workflow_id == workflow_id and not ex.is_deleted
        ]

        items.sort(key=lambda ex: ex.created_at, reverse=True)
        total = len(items)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = items[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
