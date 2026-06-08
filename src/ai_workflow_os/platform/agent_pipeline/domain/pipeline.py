"""
Agent Pipeline 聚合根

管理Agent发布流水线的完整生命周期，协调各阶段步骤的执行。
"""

from dataclasses import dataclass, field
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import (
    PIPELINE_STAGE_ORDER,
    PipelineStage,
    PipelineStatus,
    PipelineStepStatus,
)
from .pipeline_step import PipelineStep


@dataclass
class AgentPipeline(BaseEntity):
    """Agent发布流水线聚合根

    管理Agent从创建到部署的完整发布流程，确保所有阶段按序执行，
    且必须通过评估门禁才能发布。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        status: 流水线状态
        current_stage: 当前执行阶段
        steps: 流水线步骤列表
        triggered_by: 触发者标识
        metadata: 扩展元数据
    """

    agent_id: str = ""
    version_id: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: PipelineStage | None = field(default=None)
    steps: list[PipelineStep] = field(default_factory=list)
    triggered_by: str | None = field(default=None)
    metadata: dict[str, Any] = field(default_factory=dict)

    def initialize_steps(self, operator: str | None = None) -> None:
        """初始化流水线步骤

        为每个标准阶段创建待执行的步骤记录。

        Args:
            operator: 操作者标识
        """
        self.steps = [
            PipelineStep(
                pipeline_id=self.id,
                agent_id=self.agent_id,
                version_id=self.version_id,
                stage=stage,
                created_by=operator,
            )
            for stage in PIPELINE_STAGE_ORDER
        ]
        self.current_stage = PIPELINE_STAGE_ORDER[0]
        self.touch(operator)

    def start(self, operator: str | None = None) -> None:
        """启动流水线

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 流水线状态不允许启动
        """
        if self.status != PipelineStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="PIPELINE_START_STATUS",
                message=f"流水线状态为 {self.status.value}，只有待启动状态的流水线才能启动",
            )
        self.status = PipelineStatus.RUNNING
        self.triggered_by = operator
        self.touch(operator)

    def get_current_step(self) -> PipelineStep | None:
        """获取当前阶段的步骤

        Returns:
            当前步骤，若无则返回None
        """
        if self.current_stage is None:
            return None
        for step in self.steps:
            if step.stage == self.current_stage:
                return step
        return None

    def advance_to_next_stage(self, operator: str | None = None) -> PipelineStage | None:
        """推进到下一个阶段

        Args:
            operator: 操作者标识

        Returns:
            下一个阶段，若已到末尾则返回None

        Raises:
            BusinessRuleViolationException: 当前阶段未通过
        """
        current_step = self.get_current_step()
        if current_step is None:
            return None

        # 回滚阶段不参与正常推进
        if current_step.stage == PipelineStage.ROLLBACK:
            return None

        # 检查当前阶段是否通过
        if current_step.status != PipelineStepStatus.PASSED:
            raise BusinessRuleViolationException(
                rule="PIPELINE_STAGE_NOT_PASSED",
                message=(
                    f"阶段 {current_step.stage.value} 状态为 {current_step.status.value}，"
                    "只有通过的阶段才能推进到下一阶段"
                ),
            )

        # 查找下一个阶段
        current_index = PIPELINE_STAGE_ORDER.index(current_step.stage)
        if current_index + 1 >= len(PIPELINE_STAGE_ORDER):
            self.status = PipelineStatus.PASSED
            self.current_stage = None
            self.touch(operator)
            return None

        next_stage = PIPELINE_STAGE_ORDER[current_index + 1]
        self.current_stage = next_stage
        self.touch(operator)
        return next_stage

    def fail_current_stage(
        self,
        error_message: str,
        operator: str | None = None,
    ) -> None:
        """标记当前阶段失败并终止流水线

        Args:
            error_message: 错误信息
            operator: 操作者标识
        """
        current_step = self.get_current_step()
        if current_step is not None:
            current_step.fail(error_message, operator)

        self.status = PipelineStatus.FAILED
        self.touch(operator)

    def trigger_rollback(
        self,
        reason: str,
        operator: str | None = None,
    ) -> PipelineStep:
        """触发回滚

        Args:
            reason: 回滚原因
            operator: 操作者标识

        Returns:
            回滚步骤
        """
        self.status = PipelineStatus.ROLLED_BACK
        self.current_stage = PipelineStage.ROLLBACK

        # 查找或创建回滚步骤
        rollback_step = None
        for step in self.steps:
            if step.stage == PipelineStage.ROLLBACK:
                rollback_step = step
                break

        if rollback_step is None:
            rollback_step = PipelineStep(
                pipeline_id=self.id,
                agent_id=self.agent_id,
                version_id=self.version_id,
                stage=PipelineStage.ROLLBACK,
                created_by=operator,
            )
            self.steps.append(rollback_step)

        rollback_step.start(operator)
        rollback_step.complete(
            gate_passed=True,
            result_data={"reason": reason},
            operator=operator,
        )

        self.touch(operator)
        return rollback_step

    def cancel(self, operator: str | None = None) -> None:
        """取消流水线

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 流水线已终止
        """
        if self.status in (PipelineStatus.PASSED, PipelineStatus.ROLLED_BACK):
            raise BusinessRuleViolationException(
                rule="PIPELINE_CANCEL_TERMINAL",
                message=f"流水线状态为 {self.status.value}，已终止的流水线不能取消",
            )
        self.status = PipelineStatus.CANCELLED
        self.touch(operator)

    @property
    def is_evaluation_passed(self) -> bool:
        """检查评估阶段是否通过

        Returns:
            评估阶段是否通过质量门禁
        """
        for step in self.steps:
            if step.stage == PipelineStage.EVALUATION:
                return step.status == PipelineStepStatus.PASSED and step.gate_passed
        return False

    @property
    def progress_percentage(self) -> float:
        """计算流水线进度百分比

        Returns:
            进度百分比（0-100）
        """
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.is_terminal)
        return round((completed / len(self.steps)) * 100, 1)

    @property
    def total_duration_ms(self) -> float | None:
        """计算流水线总执行时长（毫秒）"""
        durations = [s.duration_ms for s in self.steps if s.duration_ms is not None]
        return sum(durations) if durations else None
