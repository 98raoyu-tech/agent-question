"""
Agent发布实体

管理Agent的发布记录，支持灰度发布和回滚。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ...common.base_entity import BaseEntity


class ReleaseStatus(str, Enum):
    """发布状态枚举"""

    PENDING = "pending"
    """待发布"""

    IN_PROGRESS = "in_progress"
    """发布中"""

    SUCCESS = "success"
    """发布成功"""

    FAILED = "failed"
    """发布失败"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


@dataclass
class AgentRelease(BaseEntity):
    """Agent发布实体

    记录Agent的发布历史和灰度配置。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        release_name: 发布名称
        status: 发布状态
        release_notes: 发布说明
        rollout_percentage: 灰度发布百分比（0-100）
        released_at: 发布时间
        rolled_back_at: 回滚时间
        metadata: 扩展元数据
    """

    agent_id: str = ""
    version_id: str = ""
    release_name: str = ""
    status: ReleaseStatus = ReleaseStatus.PENDING
    release_notes: str = ""
    rollout_percentage: int = 100
    released_at: Optional[datetime] = field(default=None)
    rolled_back_at: Optional[datetime] = field(default=None)
    metadata: dict[str, Any] = field(default_factory=dict)

    def start_release(self, operator: Optional[str] = None) -> None:
        """开始发布

        Args:
            operator: 操作者标识
        """
        self.status = ReleaseStatus.IN_PROGRESS
        self.touch(operator)

    def complete_release(self, operator: Optional[str] = None) -> None:
        """完成发布

        Args:
            operator: 操作者标识
        """
        from datetime import timezone

        self.status = ReleaseStatus.SUCCESS
        self.released_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail_release(self, error: str = "", operator: Optional[str] = None) -> None:
        """发布失败

        Args:
            error: 错误信息
            operator: 操作者标识
        """
        self.status = ReleaseStatus.FAILED
        if error:
            self.metadata["error"] = error
        self.touch(operator)

    def rollback(self, operator: Optional[str] = None) -> None:
        """回滚发布

        Args:
            operator: 操作者标识
        """
        from datetime import timezone

        self.status = ReleaseStatus.ROLLED_BACK
        self.rolled_back_at = datetime.now(timezone.utc)
        self.touch(operator)

    def set_rollout_percentage(self, percentage: int, operator: Optional[str] = None) -> None:
        """设置灰度发布百分比

        Args:
            percentage: 灰度百分比（0-100）
            operator: 操作者标识
        """
        self.rollout_percentage = max(0, min(100, percentage))
        self.touch(operator)
