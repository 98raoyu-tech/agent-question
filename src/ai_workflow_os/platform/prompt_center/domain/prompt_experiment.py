"""
Prompt实验实体

管理Prompt模板的A/B测试实验。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException, ValidationException


class ExperimentStatus(str, Enum):
    """实验状态枚举"""

    DRAFT = "draft"
    """草稿状态"""

    RUNNING = "running"
    """运行中"""

    COMPLETED = "completed"
    """已完成"""

    CANCELLED = "cancelled"
    """已取消"""


@dataclass
class PromptExperiment(BaseEntity):
    """Prompt实验实体

    管理Prompt模板的A/B测试实验，支持流量分割和结果统计。

    Attributes:
        prompt_id: 关联的Prompt模板标识
        experiment_name: 实验名称
        variant_a_version_id: 变体A的版本标识
        variant_b_version_id: 变体B的版本标识
        status: 实验状态
        traffic_split: 变体A的流量比例（0-1）
        sample_size: 样本大小
        started_at: 开始时间
        completed_at: 完成时间
        results: 实验结果统计
        winner_version_id: 获胜版本标识
    """

    prompt_id: str = ""
    experiment_name: str = ""
    variant_a_version_id: str = ""
    variant_b_version_id: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    traffic_split: float = 0.5
    sample_size: int = 0
    started_at: datetime | None = field(default=None)
    completed_at: datetime | None = field(default=None)
    results: dict[str, Any] = field(default_factory=dict)
    winner_version_id: str | None = field(default=None)

    def start(self, operator: str | None = None) -> None:
        """启动实验

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 实验状态不允许启动
        """
        if self.status != ExperimentStatus.DRAFT:
            raise BusinessRuleViolationException(
                rule="experiment_start",
                message=f"实验当前状态为{self.status.value}，无法启动",
            )

        if not self.variant_a_version_id or not self.variant_b_version_id:
            raise ValidationException(message="变体A和变体B的版本标识不能为空")

        if not 0 <= self.traffic_split <= 1:
            raise ValidationException(message="流量分割比例必须在0到1之间")

        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.touch(operator)

    def complete(
        self,
        winner_version_id: str,
        operator: str | None = None,
    ) -> None:
        """完成实验

        Args:
            winner_version_id: 获胜版本标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 实验状态不允许完成
        """
        if self.status != ExperimentStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="experiment_complete",
                message=f"实验当前状态为{self.status.value}，无法完成",
            )

        if winner_version_id not in (self.variant_a_version_id, self.variant_b_version_id):
            raise ValidationException(message="获胜版本必须是变体A或变体B")

        self.status = ExperimentStatus.COMPLETED
        self.winner_version_id = winner_version_id
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def cancel(self, operator: str | None = None) -> None:
        """取消实验

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 实验状态不允许取消
        """
        if self.status in (ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED):
            raise BusinessRuleViolationException(
                rule="experiment_cancel",
                message=f"实验当前状态为{self.status.value}，无法取消",
            )

        self.status = ExperimentStatus.CANCELLED
        self.completed_at = datetime.now(UTC)
        self.touch(operator)
