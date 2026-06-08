"""
工作流引擎枚举定义

定义工作流节点类型、工作流状态、节点状态和边条件类型等枚举。
"""

from enum import Enum


class NodeType(str, Enum):
    """工作流节点类型枚举"""

    AGENT = "agent"
    """Agent节点"""

    TOOL = "tool"
    """工具节点"""

    KNOWLEDGE = "knowledge"
    """知识检索节点"""

    CONDITION = "condition"
    """条件判断节点"""

    HUMAN = "human"
    """人工审批节点"""

    START = "start"
    """起始节点"""

    END = "end"
    """终止节点"""

    PARALLEL = "parallel"
    """并行分支节点"""

    LOOP = "loop"
    """循环节点"""


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""

    DRAFT = "draft"
    """草稿"""

    ACTIVE = "active"
    """已激活"""

    RUNNING = "running"
    """运行中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """失败"""

    CANCELLED = "cancelled"
    """已取消"""

    PAUSED = "paused"
    """已暂停"""


class NodeStatus(str, Enum):
    """节点执行状态枚举"""

    PENDING = "pending"
    """待执行"""

    RUNNING = "running"
    """执行中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """执行失败"""

    SKIPPED = "skipped"
    """已跳过"""

    WAITING = "waiting"
    """等待中"""


class EdgeConditionType(str, Enum):
    """边条件类型枚举"""

    ALWAYS = "always"
    """无条件跳转"""

    EXPRESSION = "expression"
    """表达式条件"""

    SUCCESS = "success"
    """前序节点成功时跳转"""

    FAILURE = "failure"
    """前序节点失败时跳转"""
