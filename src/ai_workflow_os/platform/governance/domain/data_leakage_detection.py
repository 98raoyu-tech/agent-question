"""
数据泄露检测实体

定义数据泄露检测的核心业务实体和相关枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class LeakageType(str, Enum):
    """泄露类型枚举"""

    TRAINING_DATA = "TRAINING_DATA"
    """训练数据泄露"""

    MEMORY_LEAK = "MEMORY_LEAK"
    """内存泄露"""

    CONTEXT_LEAK = "CONTEXT_LEAK"
    """上下文泄露"""


@dataclass
class DataLeakageDetection(BaseEntity):
    """数据泄露检测实体

    检测和管理AI系统中的数据泄露风险。

    Attributes:
        target_id: 检测目标标识
        target_type: 检测目标类型
        source_content: 源内容
        output_content: 输出内容
        leakage_type: 泄露类型
        confidence_score: 置信度分数（0-1）
        matched_segments: 匹配的泄露片段列表
        is_blocked: 是否已阻止
    """

    target_id: str = ""
    target_type: str = ""
    source_content: str = ""
    output_content: str = ""
    leakage_type: str = LeakageType.TRAINING_DATA.value
    confidence_score: float = 0.0
    matched_segments: list[dict[str, Any]] = field(default_factory=list)
    is_blocked: bool = False

    def block(self, operator: Optional[str] = None) -> None:
        """阻止数据泄露

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 无匹配泄露片段时不允许阻止
        """
        if not self.matched_segments:
            raise BusinessRuleViolationException(
                rule="leakage_block_requires_segments",
                message="未发现泄露片段，无法执行阻止操作",
            )

        self.is_blocked = True
        self.touch(operator)

    def get_leakage_report(self) -> dict[str, Any]:
        """生成泄露报告

        Returns:
            泄露报告字典
        """
        severity = self._calculate_severity()

        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "leakage_type": self.leakage_type,
            "confidence_score": self.confidence_score,
            "severity": severity,
            "matched_segments_count": len(self.matched_segments),
            "matched_segments": self.matched_segments,
            "is_blocked": self.is_blocked,
            "source_content_length": len(self.source_content),
            "output_content_length": len(self.output_content),
        }

    def _calculate_severity(self) -> str:
        """根据置信度和匹配片段计算严重程度

        Returns:
            严重程度字符串
        """
        if self.confidence_score >= 0.8 and len(self.matched_segments) >= 3:
            return "CRITICAL"
        if self.confidence_score >= 0.6 or len(self.matched_segments) >= 2:
            return "HIGH"
        if self.confidence_score >= 0.3 or self.matched_segments:
            return "MEDIUM"
        return "LOW"
