"""
工作流节点实体

定义工作流中单个节点的结构和行为，支持节点的生命周期状态管理。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ...common.base_entity import BaseEntity
from .enums import NodeStatus, NodeType


@dataclass
class WorkflowNode(BaseEntity):
    """工作流节点实体

    表示工作流中的一个执行单元，支持多种节点类型（Agent、工具、条件判断等），
    并提供节点状态的生命周期管理。

    Attributes:
        workflow_id: 所属工作流标识
        node_type: 节点类型
        name: 节点名称
        config: 节点配置
        position_x: 前端布局X坐标
        position_y: 前端布局Y坐标
        timeout_seconds: 节点执行超时时间（秒）
        retry_count: 失败重试次数
        status: 节点当前状态
        started_at: 开始执行时间
        completed_at: 完成执行时间
        error_message: 错误信息
    """

    workflow_id: str = ""
    node_type: NodeType = NodeType.AGENT
    name: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0
    timeout_seconds: int = 300
    retry_count: int = 0
    status: NodeStatus = NodeStatus.PENDING
    started_at: datetime | None = field(default=None)
    completed_at: datetime | None = field(default=None)
    error_message: str | None = field(default=None)

    def start(self, operator: str | None = None) -> None:
        """开始执行节点

        Args:
            operator: 操作者标识
        """
        self.status = NodeStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.touch(operator)

    def complete(self, operator: str | None = None) -> None:
        """标记节点执行完成

        Args:
            operator: 操作者标识
        """
        self.status = NodeStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def fail(self, error_message: str, operator: str | None = None) -> None:
        """标记节点执行失败

        Args:
            error_message: 错误信息
            operator: 操作者标识
        """
        self.status = NodeStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def skip(self, operator: str | None = None) -> None:
        """跳过节点

        Args:
            operator: 操作者标识
        """
        self.status = NodeStatus.SKIPPED
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    @property
    def is_terminal(self) -> bool:
        """判断节点是否已终止

        Returns:
            节点是否处于终态
        """
        return self.status in (
            NodeStatus.COMPLETED,
            NodeStatus.FAILED,
            NodeStatus.SKIPPED,
        )

    @property
    def duration_ms(self) -> float | None:
        """计算节点执行时长（毫秒）

        Returns:
            执行时长，若未完成则返回None
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
