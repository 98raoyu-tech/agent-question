"""
评估报告实体

定义评估报告的核心业务实体，记录单次门控评估的完整结果。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import EvaluationTargetType, GateStatus


@dataclass
class EvaluationReport(BaseEntity):
    """评估报告实体

    记录目标对象针对某个质量门控的评估结果，包含指标评分、通过状态和改进建议。

    Attributes:
        target_id: 评估目标标识
        target_type: 评估目标类型
        gate_id: 关联的门控标识
        gate_name: 关联的门控名称
        status: 评估状态
        metric_scores: 指标评分映射（MetricType值 -> 评分）
        overall_score: 综合评分（0.0 ~ 1.0）
        passed: 是否通过
        evaluated_at: 评估时间
        evaluator: 评估执行者（"auto" 或 user_id）
        details: 评估详情
        recommendations: 改进建议列表
    """

    target_id: str = ""
    target_type: EvaluationTargetType = EvaluationTargetType.AGENT
    gate_id: str = ""
    gate_name: str = ""
    status: GateStatus = GateStatus.PENDING
    metric_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = False
    evaluated_at: Optional[datetime] = field(default=None)
    evaluator: str = "auto"
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def calculate_overall_score(self) -> float:
        """计算综合评分

        对所有指标评分取算术平均值作为综合评分。
        若无指标评分则返回 0.0。

        Returns:
            综合评分（0.0 ~ 1.0）
        """
        if not self.metric_scores:
            self.overall_score = 0.0
            return self.overall_score

        total = sum(self.metric_scores.values())
        count = len(self.metric_scores)
        self.overall_score = round(total / count, 4)
        return self.overall_score

    def add_recommendation(self, text: str, operator: Optional[str] = None) -> None:
        """添加改进建议

        Args:
            text: 建议内容
            operator: 操作者标识
        """
        self.recommendations.append(text)
        self.touch(operator)
