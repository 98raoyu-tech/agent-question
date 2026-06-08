"""
质量门控实体

定义质量门控的核心业务实体，用于在发布前对Agent/Workflow/Prompt/Knowledge进行质量把关。
"""

from dataclasses import dataclass, field
from typing import Any

from ...common.base_entity import BaseEntity
from .enums import EvaluationTargetType, GateStatus


@dataclass
class QualityGate(BaseEntity):
    """质量门控实体

    描述一个质量门控的完整定义，包含评估目标类型、指标阈值和阻断策略。

    Attributes:
        name: 门控名称
        description: 门控描述
        target_type: 评估目标类型
        gate_status: 门控当前状态
        metrics_thresholds: 指标阈值映射（MetricType值 -> 阈值）
        is_blocking: 是否为阻断门控（True时阻止发布）
        priority: 优先级（数值越小优先级越高）
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    target_type: EvaluationTargetType = EvaluationTargetType.AGENT
    gate_status: GateStatus = GateStatus.PENDING
    metrics_thresholds: dict[str, float] = field(default_factory=dict)
    is_blocking: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def evaluate(self, scores: dict[str, float]) -> GateStatus:
        """根据评分执行门控评估

        遍历所有指标阈值，检查对应评分是否达标。
        全部达标则返回PASSED，否则返回FAILED。

        Args:
            scores: 指标评分映射（MetricType值 -> 评分）

        Returns:
            评估后的门控状态
        """
        if not self.metrics_thresholds:
            self.gate_status = GateStatus.PASSED
            self.touch()
            return self.gate_status

        failing_metrics = self.get_failing_metrics(scores)
        if failing_metrics:
            self.gate_status = GateStatus.FAILED
        else:
            self.gate_status = GateStatus.PASSED

        self.touch()
        return self.gate_status

    def is_passing(self, scores: dict[str, float]) -> bool:
        """检查评分是否通过门控阈值

        Args:
            scores: 指标评分映射（MetricType值 -> 评分）

        Returns:
            是否全部通过
        """
        return len(self.get_failing_metrics(scores)) == 0

    def get_failing_metrics(self, scores: dict[str, float]) -> list[str]:
        """获取未达标的指标列表

        遍历门控定义的指标阈值，对比评分找出未达标的指标。

        Args:
            scores: 指标评分映射（MetricType值 -> 评分）

        Returns:
            未达标指标名称列表
        """
        failing: list[str] = []
        for metric_name, threshold in self.metrics_thresholds.items():
            score = scores.get(metric_name)
            if score is None or score < threshold:
                failing.append(metric_name)
        return failing
