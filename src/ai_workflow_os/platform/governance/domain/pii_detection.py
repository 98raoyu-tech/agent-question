"""
PII检测实体

定义个人可识别信息(PII)检测的核心业务实体和相关枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity


class PIIType(str, Enum):
    """PII类型枚举"""

    EMAIL = "EMAIL"
    """电子邮箱"""

    PHONE = "PHONE"
    """电话号码"""

    SSN = "SSN"
    """社会安全号码"""

    CREDIT_CARD = "CREDIT_CARD"
    """信用卡号"""

    NAME = "NAME"
    """姓名"""

    ADDRESS = "ADDRESS"
    """地址"""


class RiskLevel(str, Enum):
    """风险等级枚举"""

    LOW = "LOW"
    """低风险"""

    MEDIUM = "MEDIUM"
    """中等风险"""

    HIGH = "HIGH"
    """高风险"""

    CRITICAL = "CRITICAL"
    """严重风险"""


_MASK_PLACEHOLDER_MAP: dict[str, str] = {
    PIIType.EMAIL.value: "***@***.***",
    PIIType.PHONE.value: "***-***-****",
    PIIType.SSN.value: "***-**-****",
    PIIType.CREDIT_CARD.value: "****-****-****-****",
    PIIType.NAME.value: "***",
    PIIType.ADDRESS.value: "***",
}


@dataclass
class PIIDetection(BaseEntity):
    """PII检测实体

    检测和管理内容中的个人可识别信息。

    Attributes:
        target_id: 检测目标标识
        target_type: 检测目标类型
        content_hash: 内容哈希值
        detected_pii_types: 检测到的PII类型列表
        risk_level: 风险等级
        detection_results: 检测结果列表（包含position, type, confidence）
        is_masked: 是否已脱敏
        masked_content: 脱敏后的内容
    """

    target_id: str = ""
    target_type: str = ""
    content_hash: str = ""
    detected_pii_types: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    detection_results: list[dict[str, Any]] = field(default_factory=list)
    is_masked: bool = False
    masked_content: str = ""

    def mask_pii(self, operator: Optional[str] = None) -> None:
        """对检测到的PII进行脱敏处理

        遍历所有检测结果，将原始内容中对应位置的PII替换为占位符。

        Args:
            operator: 操作者标识
        """
        if not self.detection_results:
            return

        if self.masked_content:
            content = self.masked_content
        else:
            content = self.content_hash

        sorted_results = sorted(
            self.detection_results,
            key=lambda r: r.get("position", {}).get("start", 0),
            reverse=True,
        )

        for result in sorted_results:
            pii_type = result.get("type", "")
            position = result.get("position", {})
            start = position.get("start", 0)
            end = position.get("end", 0)
            placeholder = _MASK_PLACEHOLDER_MAP.get(pii_type, "***")
            content = content[:start] + placeholder + content[end:]

        self.masked_content = content
        self.is_masked = True
        self.touch(operator)

    def is_safe(self) -> bool:
        """判断内容是否安全（无PII或已脱敏）

        Returns:
            是否安全
        """
        if not self.detected_pii_types:
            return True
        return self.is_masked

    def get_detection_summary(self) -> dict[str, Any]:
        """获取检测摘要

        Returns:
            检测摘要字典
        """
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "content_hash": self.content_hash,
            "detected_pii_types": self.detected_pii_types,
            "risk_level": self.risk_level.value,
            "total_detections": len(self.detection_results),
            "is_masked": self.is_masked,
            "is_safe": self.is_safe(),
        }
