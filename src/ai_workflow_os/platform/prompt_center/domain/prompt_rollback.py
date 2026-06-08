"""
Prompt回滚实体

管理Prompt模板版本的回滚操作。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class RollbackStatus(str, Enum):
    """回滚状态枚举"""

    PENDING = "pending"
    """待执行"""

    IN_PROGRESS = "in_progress"
    """执行中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """执行失败"""


@dataclass
class PromptRollback(BaseEntity):
    """Prompt回滚实体

    管理Prompt模板版本的回滚操作，记录回滚过程和结果。

    Attributes:
        prompt_id: 关联的Prompt模板标识
        from_version_id: 来源版本标识
        to_version_id: 目标版本标识
        reason: 回滚原因
        status: 回滚状态
        initiated_by: 发起人标识
        completed_at: 完成时间
    """

    prompt_id: str = ""
    from_version_id: str = ""
    to_version_id: str = ""
    reason: str = ""
    status: RollbackStatus = RollbackStatus.PENDING
    initiated_by: str = ""
    completed_at: datetime | None = field(default=None)

    def start(self, operator: str | None = None) -> None:
        """开始回滚

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许开始
        """
        if self.status != RollbackStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="rollback_start",
                message=f"回滚当前状态为{self.status.value}，无法开始",
            )

        self.status = RollbackStatus.IN_PROGRESS
        self.touch(operator)

    def complete(self, operator: str | None = None) -> None:
        """完成回滚

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许完成
        """
        if self.status != RollbackStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="rollback_complete",
                message=f"回滚当前状态为{self.status.value}，无法完成",
            )

        self.status = RollbackStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.touch(operator)

    def fail(self, error: str, operator: str | None = None) -> None:
        """标记回滚失败

        Args:
            error: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许失败
        """
        if self.status != RollbackStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="rollback_fail",
                message=f"回滚当前状态为{self.status.value}，无法标记为失败",
            )

        self.status = RollbackStatus.FAILED
        self.reason = f"{self.reason}\n\nError: {error}"
        self.completed_at = datetime.now(UTC)
        self.touch(operator)
