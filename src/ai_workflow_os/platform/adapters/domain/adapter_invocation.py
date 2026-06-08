"""
适配器调用实体

记录Agent适配器的每次调用详情，包括输入输出、状态、延迟和Token使用量。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ...common.base_entity import BaseEntity
from .enums import AdapterType, InvocationStatus


@dataclass
class AdapterInvocation(BaseEntity):
    """适配器调用实体

    记录一次完整的Agent适配器调用过程，包括调用输入、输出、状态转换和性能指标。

    Attributes:
        adapter_type: 适配器类型
        agent_id: Agent标识
        input_data: 输入数据
        output_data: 输出数据
        status: 调用状态
        started_at: 开始时间
        completed_at: 完成时间
        error_message: 错误信息
        latency_ms: 延迟（毫秒）
        token_usage: Token使用量
    """

    adapter_type: AdapterType = AdapterType.LANGCHAIN
    agent_id: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    status: InvocationStatus = InvocationStatus.PENDING
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = field(default=None)
    error_message: str | None = field(default=None)
    latency_ms: float | None = field(default=None)
    token_usage: dict[str, Any] | None = field(default=None)

    def complete(self, output_data: dict[str, Any], operator: str | None = None) -> None:
        """标记调用为已完成

        Args:
            output_data: 输出数据
            operator: 操作者标识
        """
        self.output_data = output_data
        self.status = InvocationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self._calculate_latency()
        self.touch(operator)

    def fail(self, error_message: str, operator: str | None = None) -> None:
        """标记调用为失败

        Args:
            error_message: 错误信息
            operator: 操作者标识
        """
        self.status = InvocationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
        self._calculate_latency()
        self.touch(operator)

    def timeout(self, operator: str | None = None) -> None:
        """标记调用为超时

        Args:
            operator: 操作者标识
        """
        self.status = InvocationStatus.TIMEOUT
        self.error_message = "调用执行超时"
        self.completed_at = datetime.now(UTC)
        self._calculate_latency()
        self.touch(operator)

    def _calculate_latency(self) -> None:
        """计算调用延迟（毫秒）"""
        if self.completed_at is not None:
            delta = self.completed_at - self.started_at
            self.latency_ms = delta.total_seconds() * 1000
