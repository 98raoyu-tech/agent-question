"""
风险评估引擎实体

定义风险评估的核心业务实体。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .pii_detection import RiskLevel


@dataclass
class RiskAssessment(BaseEntity):
    """风险评估实体

    管理目标对象的风险评估结果和决策流程。

    Attributes:
        target_id: 评估目标标识
        target_type: 评估目标类型
        risk_score: 风险分数（0-100）
        risk_level: 风险等级
        risk_factors: 风险因素列表（包含factor_name, weight, description）
        recommendations: 改进建议列表
        assessed_at: 评估时间
        assessor: 评估者标识
        is_accepted: 是否已接受风险
        accepted_by: 风险接受者标识
    """

    target_id: str = ""
    target_type: str = ""
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assessor: str = ""
    is_accepted: bool = False
    accepted_by: Optional[str] = None

    def accept_risk(self, user: str, operator: Optional[str] = None) -> None:
        """接受风险

        Args:
            user: 接受风险的用户标识
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 严重风险不可接受
        """
        if self.risk_level == RiskLevel.CRITICAL:
            raise BusinessRuleViolationException(
                rule="critical_risk_not_acceptable",
                message="严重风险等级不允许被接受，必须先进行缓解处理",
            )

        self.is_accepted = True
        self.accepted_by = user
        self.touch(operator)

    def reject_risk(self, user: str, operator: Optional[str] = None) -> None:
        """拒绝风险

        Args:
            user: 拒绝风险的用户标识
            operator: 操作者标识
        """
        self.is_accepted = False
        self.accepted_by = user
        self.touch(operator)

    def recalculate(self, operator: Optional[str] = None) -> None:
        """根据风险因素重新计算风险分数

        遍历所有风险因素，基于权重计算加权平均分。

        Args:
            operator: 操作者标识
        """
        if not self.risk_factors:
            self.risk_score = 0.0
            self.risk_level = RiskLevel.LOW
            self.touch(operator)
            return

        total_weight = sum(f.get("weight", 0) for f in self.risk_factors)
        if total_weight <= 0:
            self.risk_score = 0.0
            self.risk_level = RiskLevel.LOW
            self.touch(operator)
            return

        weighted_score = sum(
            f.get("score", 0) * f.get("weight", 0) for f in self.risk_factors
        )
        self.risk_score = round(weighted_score / total_weight, 2)

        self.risk_level = self._determine_risk_level(self.risk_score)
        self.touch(operator)

    def add_risk_factor(self, factor: dict[str, Any], operator: Optional[str] = None) -> None:
        """添加风险因素

        Args:
            factor: 风险因素字典，需包含factor_name, weight, description, score
            operator: 操作者标识
        """
        self.risk_factors.append(factor)
        self.recalculate(operator)

    @staticmethod
    def _determine_risk_level(score: float) -> RiskLevel:
        """根据分数判定风险等级

        Args:
            score: 风险分数

        Returns:
            风险等级枚举值
        """
        if score >= 80:
            return RiskLevel.CRITICAL
        if score >= 60:
            return RiskLevel.HIGH
        if score >= 30:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
