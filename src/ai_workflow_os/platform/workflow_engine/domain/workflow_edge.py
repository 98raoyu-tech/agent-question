"""
工作流边实体

定义工作流中节点之间的连接关系和跳转条件。
"""

from dataclasses import dataclass, field

from ...common.base_entity import BaseEntity
from .enums import EdgeConditionType


@dataclass
class WorkflowEdge(BaseEntity):
    """工作流边实体

    表示工作流中两个节点之间的有向连接，支持多种条件类型的跳转控制。

    Attributes:
        workflow_id: 所属工作流标识
        source_node_id: 源节点标识
        target_node_id: 目标节点标识
        condition_type: 条件类型
        condition_expression: 条件表达式（可选）
        priority: 优先级，数值越大优先级越高
    """

    workflow_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    condition_type: EdgeConditionType = EdgeConditionType.ALWAYS
    condition_expression: str | None = field(default=None)
    priority: int = 0
