"""
事故实体

定义Agent事故的核心业务实体，包含事故生命周期管理、状态流转和时间线记录。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import (
    Environment,
    IncidentSeverity,
    IncidentStatus,
)


@dataclass
class TimelineEntry:
    """时间线条目值对象

    Attributes:
        timestamp: 时间戳
        action: 操作描述
        operator: 操作者
        details: 详细信息
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    action: str = ""
    operator: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Incident(BaseEntity):
    """事故实体

    管理Agent事故的完整生命周期，包括发现、调查、缓解、解决和关闭。

    Attributes:
        agent_id: Agent标识
        title: 事故标题
        description: 事故描述
        severity: 严重程度
        status: 事故状态
        assigned_to: 分配给
        environment: 发生环境
        detected_at: 检测时间
        resolved_at: 解决时间
        root_cause: 根本原因
        resolution: 解决方案
        timeline: 时间线记录
    """

    agent_id: str = ""
    title: str = ""
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.LOW
    status: IncidentStatus = IncidentStatus.OPEN
    assigned_to: Optional[str] = None
    environment: Environment = Environment.DEV
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    timeline: list[TimelineEntry] = field(default_factory=list)

    def assign(self, user: str, operator: Optional[str] = None) -> None:
        """分配事故给用户

        Args:
            user: 目标用户标识
            operator: 操作者标识
        """
        self.assigned_to = user
        self.add_timeline_entry(
            TimelineEntry(
                action="assigned",
                operator=operator,
                details={"assigned_to": user},
            ),
            operator,
        )

    def investigate(self, operator: Optional[str] = None) -> None:
        """开始调查事故

        Args:
            operator: 操作者标识

        Raises:
            ValueError: 事故状态不允许开始调查
        """
        # 只有打开状态的事故才能开始调查
        if self.status != IncidentStatus.OPEN:
            raise ValueError(f"当前状态 {self.status.value} 不允许开始调查")

        self.status = IncidentStatus.INVESTIGATING
        self.add_timeline_entry(
            TimelineEntry(
                action="investigating",
                operator=operator,
                details={"message": "开始调查事故"},
            ),
            operator,
        )

    def mitigate(self, operator: Optional[str] = None) -> None:
        """缓解事故

        Args:
            operator: 操作者标识

        Raises:
            ValueError: 事故状态不允许缓解
        """
        # 只有调查中状态才能缓解
        if self.status != IncidentStatus.INVESTIGATING:
            raise ValueError(f"当前状态 {self.status.value} 不允许缓解")

        self.status = IncidentStatus.MITIGATED
        self.add_timeline_entry(
            TimelineEntry(
                action="mitigated",
                operator=operator,
                details={"message": "事故已缓解"},
            ),
            operator,
        )

    def resolve(
        self,
        root_cause: str,
        resolution: str,
        operator: Optional[str] = None,
    ) -> None:
        """解决事故

        Args:
            root_cause: 根本原因
            resolution: 解决方案
            operator: 操作者标识

        Raises:
            ValueError: 事故状态不允许解决
        """
        # 只有缓解状态才能解决
        if self.status != IncidentStatus.MITIGATED:
            raise ValueError(f"当前状态 {self.status.value} 不允许解决")

        self.status = IncidentStatus.RESOLVED
        self.root_cause = root_cause
        self.resolution = resolution
        self.resolved_at = datetime.now(timezone.utc)
        self.add_timeline_entry(
            TimelineEntry(
                action="resolved",
                operator=operator,
                details={
                    "root_cause": root_cause,
                    "resolution": resolution,
                },
            ),
            operator,
        )

    def close(self, operator: Optional[str] = None) -> None:
        """关闭事故

        Args:
            operator: 操作者标识

        Raises:
            ValueError: 事故状态不允许关闭
        """
        # 只有解决状态才能关闭
        if self.status != IncidentStatus.RESOLVED:
            raise ValueError(f"当前状态 {self.status.value} 不允许关闭")

        self.status = IncidentStatus.CLOSED
        self.add_timeline_entry(
            TimelineEntry(
                action="closed",
                operator=operator,
                details={"message": "事故已关闭"},
            ),
            operator,
        )

    def add_timeline_entry(self, entry: TimelineEntry, operator: Optional[str] = None) -> None:
        """添加时间线条目

        Args:
            entry: 时间线条目
            operator: 操作者标识
        """
        if operator and not entry.operator:
            entry.operator = operator
        if not entry.timestamp:
            entry.timestamp = datetime.now(timezone.utc)

        self.timeline.append(entry)
        self.touch(operator)

    def get_duration_minutes(self) -> Optional[float]:
        """获取事故持续时间（分钟）

        Returns:
            持续时间，未解决返回None
        """
        if self.resolved_at is None:
            return None

        delta = self.resolved_at - self.detected_at
        return delta.total_seconds() / 60
