"""
成本告警实体

定义成本告警的核心业务实体，支持阈值告警、预测告警、突增告警和异常告警。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import ValidationException


class AlertType(str, Enum):
    """告警类型枚举"""

    THRESHOLD = "threshold"
    """阈值告警：当前使用量超过设定阈值"""

    FORECAST = "forecast"
    """预测告警：预测成本将超出预算"""

    SPIKE = "spike"
    """突增告警：成本出现异常突增"""

    ANOMALY = "anomaly"
    """异常告警：成本模式出现异常"""


class AlertSeverity(str, Enum):
    """告警严重级别枚举"""

    INFO = "info"
    """信息"""

    WARNING = "warning"
    """警告"""

    CRITICAL = "critical"
    """严重"""


class AlertTargetType(str, Enum):
    """告警目标类型枚举"""

    AGENT = "agent"
    """Agent"""

    WORKFLOW = "workflow"
    """工作流"""

    PROJECT = "project"
    """项目"""

    TENANT = "tenant"
    """租户"""


@dataclass
class CostAlert(BaseEntity):
    """成本告警实体

    当成本使用触发预设条件时生成告警，支持多级别告警和告警确认机制。

    Attributes:
        budget_id: 关联的预算标识
        target_id: 告警目标标识
        target_type: 告警目标类型
        alert_type: 告警类型
        severity: 告警严重级别
        message: 告警消息
        threshold_percentage: 阈值百分比
        current_percentage: 当前百分比
        triggered_at: 告警触发时间
        acknowledged: 是否已确认
        acknowledged_by: 确认者标识
    """

    budget_id: str = ""
    target_id: str = ""
    target_type: AlertTargetType = AlertTargetType.AGENT
    alert_type: AlertType = AlertType.THRESHOLD
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    threshold_percentage: float = 0.0
    current_percentage: float = 0.0
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None

    def acknowledge(
        self,
        user: str,
        operator: Optional[str] = None,
    ) -> None:
        """确认告警

        Args:
            user: 确认者标识
            operator: 操作者标识

        Raises:
            ValidationException: 告警已被确认
        """
        if self.acknowledged:
            raise ValidationException(
                message=f"告警 [{self.id}] 已被 {self.acknowledged_by} 确认，不可重复确认"
            )

        self.acknowledged = True
        self.acknowledged_by = user
        self.touch(operator)

    def is_acknowledged(self) -> bool:
        """判断告警是否已确认

        Returns:
            是否已确认
        """
        return self.acknowledged
