"""
合规记录实体

定义合规检查的核心业务实体和相关枚举。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity


class ComplianceFramework(str, Enum):
    """合规框架枚举"""

    GDPR = "GDPR"
    """通用数据保护条例"""

    SOC2 = "SOC2"
    """SOC 2审计标准"""

    HIPAA = "HIPAA"
    """健康保险可携性与责任法案"""

    CUSTOM = "CUSTOM"
    """自定义合规框架"""


class ComplianceStatus(str, Enum):
    """合规状态枚举"""

    COMPLIANT = "COMPLIANT"
    """完全合规"""

    NON_COMPLIANT = "NON_COMPLIANT"
    """不合规"""

    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    """部分合规"""

    UNDER_REVIEW = "UNDER_REVIEW"
    """审核中"""


@dataclass
class ComplianceRecord(BaseEntity):
    """合规记录实体

    管理目标对象在特定合规框架下的检查记录。

    Attributes:
        target_id: 检查目标标识
        target_type: 检查目标类型
        compliance_framework: 合规框架
        status: 合规状态
        findings: 检查发现列表（包含finding_id, severity, description, category）
        remediation_actions: 整改措施列表（包含action_id, description, assignee, due_date, status）
        assessed_at: 评估时间
        next_review_at: 下次审查时间
    """

    target_id: str = ""
    target_type: str = ""
    compliance_framework: str = ComplianceFramework.CUSTOM.value
    status: str = ComplianceStatus.UNDER_REVIEW.value
    findings: list[dict[str, Any]] = field(default_factory=list)
    remediation_actions: list[dict[str, Any]] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    next_review_at: Optional[datetime] = None

    def add_finding(self, finding: dict[str, Any], operator: Optional[str] = None) -> None:
        """添加合规检查发现

        Args:
            finding: 发现详情，需包含finding_id, severity, description, category
            operator: 操作者标识
        """
        self.findings.append(finding)
        self.touch(operator)

    def add_remediation(self, action: dict[str, Any], operator: Optional[str] = None) -> None:
        """添加整改措施

        Args:
            action: 整改措施详情，需包含action_id, description, assignee, due_date, status
            operator: 操作者标识
        """
        self.remediation_actions.append(action)
        self.touch(operator)

    def mark_compliant(self, operator: Optional[str] = None) -> None:
        """标记为合规

        Args:
            operator: 操作者标识
        """
        self.status = ComplianceStatus.COMPLIANT.value
        self.touch(operator)

    def mark_non_compliant(self, operator: Optional[str] = None) -> None:
        """标记为不合规

        Args:
            operator: 操作者标识
        """
        self.status = ComplianceStatus.NON_COMPLIANT.value
        self.touch(operator)
