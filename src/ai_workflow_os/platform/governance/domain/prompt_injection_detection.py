"""
提示注入检测实体

定义Prompt注入检测的核心业务实体和相关枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class InjectionType(str, Enum):
    """注入类型枚举"""

    DIRECT = "DIRECT"
    """直接注入"""

    INDIRECT = "INDIRECT"
    """间接注入"""

    JAILBREAK = "JAILBREAK"
    """越狱攻击"""

    CONTEXT_MANIPULATION = "CONTEXT_MANIPULATION"
    """上下文操纵"""


@dataclass
class PromptInjectionDetection(BaseEntity):
    """提示注入检测实体

    检测和管理Prompt注入攻击。

    Attributes:
        target_id: 检测目标标识
        prompt_content: 提示内容
        is_injection_detected: 是否检测到注入
        injection_type: 注入类型
        confidence_score: 置信度分数（0-1）
        detection_details: 检测详情
        blocked: 是否已阻止
        mitigation_action: 缓解措施
    """

    target_id: str = ""
    prompt_content: str = ""
    is_injection_detected: bool = False
    injection_type: str = InjectionType.DIRECT.value
    confidence_score: float = 0.0
    detection_details: dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    mitigation_action: str = ""

    def block(self, operator: Optional[str] = None) -> None:
        """阻止该提示请求

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 未检测到注入时不允许阻止
        """
        if not self.is_injection_detected:
            raise BusinessRuleViolationException(
                rule="injection_block_requires_detection",
                message="未检测到注入攻击，无法执行阻止操作",
            )

        self.blocked = True
        self.mitigation_action = "BLOCKED"
        self.touch(operator)

    def allow(self, operator: Optional[str] = None) -> None:
        """允许该提示请求通过

        Args:
            operator: 操作者标识
        """
        self.blocked = False
        self.mitigation_action = "ALLOWED"
        self.touch(operator)

    def get_risk_assessment(self) -> dict[str, Any]:
        """获取风险评估信息

        Returns:
            风险评估字典
        """
        if self.confidence_score >= 0.8:
            risk_level = "CRITICAL"
        elif self.confidence_score >= 0.6:
            risk_level = "HIGH"
        elif self.confidence_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "target_id": self.target_id,
            "is_injection_detected": self.is_injection_detected,
            "injection_type": self.injection_type,
            "confidence_score": self.confidence_score,
            "risk_level": risk_level,
            "blocked": self.blocked,
            "mitigation_action": self.mitigation_action,
            "detection_details": self.detection_details,
        }
