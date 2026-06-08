"""
流水线步骤实体

定义流水线中单个阶段的执行记录。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ...common.base_entity import BaseEntity
from .enums import PipelineStage, PipelineStepStatus


@dataclass
class PipelineStep(BaseEntity):
    """流水线步骤实体

    记录流水线中单个阶段的执行状态和结果。

    Attributes:
        pipeline_id: 关联的流水线标识
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        stage: 流水线阶段
        status: 步骤状态
        started_at: 开始时间
        completed_at: 完成时间
        error_message: 错误信息
        result_data: 步骤结果数据
        gate_passed: 是否通过质量门禁
        trace_id: 链路追踪标识
    """

    pipeline_id: str = ""
    agent_id: str = ""
    version_id: str = ""
    stage: PipelineStage = PipelineStage.CREATE
    status: PipelineStepStatus = PipelineStepStatus.PENDING
    started_at: datetime | None = field(default=None)
    completed_at: datetime | None = field(default=None)
    error_message: str | None = field(default=None)
    result_data: dict[str, Any] = field(default_factory=dict)
    gate_passed: bool = False
    trace_id: str | None = field(default=None)

    def start(self, operator: str | None = None) -> None:
        """开始执行步骤

        Args:
            operator: 操作者标识
        """
        self.status = PipelineStepStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.touch(operator)

    def complete(
        self,
        gate_passed: bool = True,
        result_data: dict[str, Any] | None = None,
        operator: str | None = None,
    ) -> None:
        """完成步骤

        Args:
            gate_passed: 是否通过质量门禁
            result_data: 步骤结果数据
            operator: 操作者标识
        """
        self.status = PipelineStepStatus.PASSED if gate_passed else PipelineStepStatus.BLOCKED
        self.gate_passed = gate_passed
        self.completed_at = datetime.now(UTC)
        if result_data:
            self.result_data = result_data
        self.touch(operator)

    def fail(self, error_message: str, operator: str | None = None) -> None:
        """标记步骤失败

        Args:
            error_message: 错误信息
            operator: 操作者标识
        """
        self.status = PipelineStepStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def skip(self, operator: str | None = None) -> None:
        """跳过步骤

        Args:
            operator: 操作者标识
        """
        self.status = PipelineStepStatus.SKIPPED
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    @property
    def is_terminal(self) -> bool:
        """判断步骤是否已终止"""
        return self.status in (
            PipelineStepStatus.PASSED,
            PipelineStepStatus.FAILED,
            PipelineStepStatus.SKIPPED,
            PipelineStepStatus.BLOCKED,
        )

    @property
    def duration_ms(self) -> float | None:
        """计算步骤执行时长（毫秒）"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
