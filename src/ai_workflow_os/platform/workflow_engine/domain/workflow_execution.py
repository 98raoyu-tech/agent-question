"""
工作流执行实体

记录工作流的一次完整执行过程，包括节点状态跟踪、输入输出和执行控制。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import NodeStatus, WorkflowStatus


@dataclass
class WorkflowExecution(BaseEntity):
    """工作流执行实体

    记录工作流的一次完整执行实例，跟踪每个节点的执行状态，
    管理执行的输入输出数据和生命周期。

    Attributes:
        workflow_id: 关联的工作流标识
        status: 执行状态
        current_node_id: 当前执行节点标识
        node_states: 节点状态映射（node_id -> status）
        input_data: 执行输入数据
        output_data: 执行输出数据
        started_at: 开始执行时间
        completed_at: 完成执行时间
        error_message: 错误信息
    """

    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_node_id: str | None = field(default=None)
    node_states: dict[str, NodeStatus] = field(default_factory=dict)
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = field(default=None)
    error_message: str | None = field(default=None)

    def advance_to_node(self, node_id: str, operator: str | None = None) -> None:
        """推进执行到指定节点

        将指定节点状态设为待执行并更新当前节点指针。

        Args:
            node_id: 目标节点标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 执行已终止
        """
        self._ensure_running("advance_to_node")
        self.current_node_id = node_id
        if node_id not in self.node_states:
            self.node_states[node_id] = NodeStatus.PENDING
        self.touch(operator)

    def complete_node(
        self,
        node_id: str,
        result_data: dict[str, Any] | None = None,
        operator: str | None = None,
    ) -> None:
        """标记节点执行完成

        Args:
            node_id: 节点标识
            result_data: 节点执行结果数据
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 执行已终止
        """
        self._ensure_running("complete_node")
        self.node_states[node_id] = NodeStatus.COMPLETED
        if result_data:
            self.output_data.update(result_data)
        self.touch(operator)

    def fail_node(
        self,
        node_id: str,
        error_message: str,
        operator: str | None = None,
    ) -> None:
        """标记节点执行失败

        Args:
            node_id: 节点标识
            error_message: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 执行已终止
        """
        self._ensure_running("fail_node")
        self.node_states[node_id] = NodeStatus.FAILED
        self.touch(operator)

    def complete(self, output_data: dict[str, Any] | None = None, operator: str | None = None) -> None:
        """标记执行完成

        Args:
            output_data: 最终输出数据
            operator: 操作者标识
        """
        self.status = WorkflowStatus.COMPLETED
        if output_data:
            self.output_data.update(output_data)
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def fail(self, error_message: str, operator: str | None = None) -> None:
        """标记执行失败

        Args:
            error_message: 错误信息
            operator: 操作者标识
        """
        self.status = WorkflowStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def _ensure_running(self, operation: str) -> None:
        """确保执行处于运行中状态

        Args:
            operation: 操作名称

        Raises:
            BusinessRuleViolationException: 执行已终止
        """
        if self.status != WorkflowStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="EXECUTION_NOT_RUNNING",
                message=f"操作 [{operation}] 仅在运行中状态下允许，当前状态: {self.status.value}",
            )

    @property
    def duration_ms(self) -> float | None:
        """计算执行总时长（毫秒）

        Returns:
            执行时长，若未完成则返回None
        """
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    @property
    def completed_node_count(self) -> int:
        """统计已完成的节点数量

        Returns:
            已完成节点数
        """
        return sum(1 for s in self.node_states.values() if s == NodeStatus.COMPLETED)

    @property
    def failed_node_count(self) -> int:
        """统计失败的节点数量

        Returns:
            失败节点数
        """
        return sum(1 for s in self.node_states.values() if s == NodeStatus.FAILED)
