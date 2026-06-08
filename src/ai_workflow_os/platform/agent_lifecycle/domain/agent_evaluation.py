"""
Agent评估实体

记录Agent版本的质量评估指标，包括准确性、延迟、成本、安全性和总体评分。
支持质量门禁检查。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import EvaluationStatus


@dataclass
class AgentEvaluation(BaseEntity):
    """Agent评估实体

    评估Agent版本的综合质量指标，用于质量门禁决策。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        evaluation_name: 评估名称
        status: 评估状态
        accuracy: 准确率（0.0 ~ 1.0）
        latency_ms: 平均延迟（毫秒）
        cost: 单次调用成本
        success_rate: 成功率（0.0 ~ 1.0）
        hallucination_rate: 幻觉率（0.0 ~ 1.0）
        groundedness_score: 基于事实评分（0.0 ~ 1.0）
        safety_score: 安全评分（0.0 ~ 1.0）
        overall_score: 综合评分（0.0 ~ 1.0）
        passed: 是否通过质量门禁
        threshold_config: 质量阈值配置
    """

    agent_id: str = ""
    version_id: str = ""
    evaluation_name: str = ""
    status: EvaluationStatus = EvaluationStatus.PENDING
    accuracy: float = 0.0
    latency_ms: float = 0.0
    cost: float = 0.0
    success_rate: float = 0.0
    hallucination_rate: float = 0.0
    groundedness_score: float = 0.0
    safety_score: float = 0.0
    overall_score: float = 0.0
    passed: bool = False
    threshold_config: dict[str, Any] = field(default_factory=dict)

    def calculate_overall_score(self) -> float:
        """计算综合评分

        基于各维度指标的加权平均计算综合评分。

        Returns:
            综合评分（0.0 ~ 1.0）
        """
        weights = {
            "accuracy": 0.30,
            "success_rate": 0.20,
            "safety_score": 0.20,
            "groundedness_score": 0.15,
            "hallucination_rate": 0.15,
        }
        hallucination_quality = 1.0 - self.hallucination_rate
        self.overall_score = (
            self.accuracy * weights["accuracy"]
            + self.success_rate * weights["success_rate"]
            + self.safety_score * weights["safety_score"]
            + self.groundedness_score * weights["groundedness_score"]
            + hallucination_quality * weights["hallucination_rate"]
        )
        self.overall_score = round(self.overall_score, 4)
        return self.overall_score

    def check_quality_gate(self, thresholds: Optional[dict[str, float]] = None) -> bool:
        """检查是否通过质量门禁

        将各项指标与阈值进行比较，全部满足则通过。

        Args:
            thresholds: 质量阈值配置，若为None则使用内置阈值配置

        Returns:
            是否通过质量门禁
        """
        effective_thresholds = thresholds or self.threshold_config

        default_thresholds = {
            "accuracy": 0.8,
            "success_rate": 0.9,
            "safety_score": 0.95,
            "hallucination_rate": 0.1,
            "groundedness_score": 0.8,
            "overall_score": 0.8,
        }

        for key, default_value in default_thresholds.items():
            if key not in effective_thresholds:
                effective_thresholds[key] = default_value

        gate_checks = [
            self.accuracy >= effective_thresholds.get("accuracy", 0.0),
            self.success_rate >= effective_thresholds.get("success_rate", 0.0),
            self.safety_score >= effective_thresholds.get("safety_score", 0.0),
            self.hallucination_rate <= effective_thresholds.get("hallucination_rate", 1.0),
            self.groundedness_score >= effective_thresholds.get("groundedness_score", 0.0),
        ]

        if effective_thresholds.get("overall_score"):
            gate_checks.append(
                self.overall_score >= effective_thresholds["overall_score"]
            )

        self.passed = all(gate_checks)
        return self.passed
