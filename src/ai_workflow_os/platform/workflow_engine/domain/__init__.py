"""
工作流引擎领域层

定义工作流引擎相关的领域实体、枚举和聚合根。
"""

from .enums import EdgeConditionType, NodeStatus, NodeType, WorkflowStatus
from .workflow_definition import WorkflowDefinition
from .workflow_edge import WorkflowEdge
from .workflow_execution import WorkflowExecution
from .workflow_node import WorkflowNode
