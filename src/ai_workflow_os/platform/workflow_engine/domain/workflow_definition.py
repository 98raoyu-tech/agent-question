"""
工作流定义聚合根

管理工作流的完整定义，包括节点、边、变量和状态转换。
"""

from dataclasses import dataclass, field
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException, ResourceNotFoundException
from .enums import WorkflowStatus
from .workflow_edge import WorkflowEdge
from .workflow_node import WorkflowNode


@dataclass
class WorkflowDefinition(BaseEntity):
    """工作流定义聚合根

    管理工作流的完整结构定义，包括节点集合、边集合和全局变量。
    提供工作流的状态激活与停用控制。

    Attributes:
        name: 工作流名称
        description: 工作流描述
        status: 工作流状态
        nodes: 节点列表
        edges: 边列表
        variables: 全局变量
        workflow_version: 工作流版本号
    """

    name: str = ""
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    workflow_version: str = "1.0.0"

    def add_node(self, node: WorkflowNode, operator: str | None = None) -> None:
        """添加节点到工作流

        Args:
            node: 待添加的节点
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非草稿状态下不允许修改
        """
        self._ensure_draft_state("add_node")
        self.nodes.append(node)
        self.touch(operator)

    def remove_node(self, node_id: str, operator: str | None = None) -> None:
        """从工作流中移除节点

        同时移除与该节点关联的所有边。

        Args:
            node_id: 待移除的节点标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非草稿状态下不允许修改
            ResourceNotFoundException: 节点不存在
        """
        self._ensure_draft_state("remove_node")

        # 移除关联的边
        self.edges = [
            edge for edge in self.edges
            if edge.source_node_id != node_id and edge.target_node_id != node_id
        ]

        # 移除节点
        original_count = len(self.nodes)
        self.nodes = [node for node in self.nodes if node.id != node_id]
        if len(self.nodes) == original_count:
            raise ResourceNotFoundException(
                resource_type="WorkflowNode",
                resource_id=node_id,
            )

        self.touch(operator)

    def add_edge(self, edge: WorkflowEdge, operator: str | None = None) -> None:
        """添加边到工作流

        Args:
            edge: 待添加的边
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非草稿状态下不允许修改
        """
        self._ensure_draft_state("add_edge")
        self.edges.append(edge)
        self.touch(operator)

    def remove_edge(self, edge_id: str, operator: str | None = None) -> None:
        """从工作流中移除边

        Args:
            edge_id: 待移除的边标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非草稿状态下不允许修改
            ResourceNotFoundException: 边不存在
        """
        self._ensure_draft_state("remove_edge")

        original_count = len(self.edges)
        self.edges = [edge for edge in self.edges if edge.id != edge_id]
        if len(self.edges) == original_count:
            raise ResourceNotFoundException(
                resource_type="WorkflowEdge",
                resource_id=edge_id,
            )

        self.touch(operator)

    def activate(self, operator: str | None = None) -> None:
        """激活工作流

        仅草稿状态的工作流可以被激活。

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非草稿状态不允许激活
        """
        if self.status != WorkflowStatus.DRAFT:
            raise BusinessRuleViolationException(
                rule="WORKFLOW_ACTIVATE_STATUS",
                message=f"工作流状态为 {self.status.value}，只有草稿状态的工作流才能激活",
            )
        self.status = WorkflowStatus.ACTIVE
        self.touch(operator)

    def deactivate(self, operator: str | None = None) -> None:
        """停用工作流

        仅激活状态的工作流可以被停用。

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 非激活状态不允许停用
        """
        if self.status != WorkflowStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="WORKFLOW_DEACTIVATE_STATUS",
                message=f"工作流状态为 {self.status.value}，只有激活状态的工作流才能停用",
            )
        self.status = WorkflowStatus.DRAFT
        self.touch(operator)

    def _ensure_draft_state(self, operation: str) -> None:
        """确保工作流处于草稿状态

        Args:
            operation: 操作名称

        Raises:
            BusinessRuleViolationException: 非草稿状态
        """
        if self.status != WorkflowStatus.DRAFT:
            raise BusinessRuleViolationException(
                rule="WORKFLOW_MODIFY_DRAFT_ONLY",
                message=f"操作 [{operation}] 仅在草稿状态下允许，当前状态: {self.status.value}",
            )
