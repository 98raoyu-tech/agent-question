"""
Agent回滚实体

记录Agent部署的回滚操作，支持回滚流程的完整生命周期管理。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import RollbackStatus


@dataclass
class AgentRollback(BaseEntity):
    """Agent回滚实体

    记录一次回滚操作的完整信息。

    Attributes:
        agent_id: 关联的Agent标识
        from_version_id: 回滚源版本标识
        to_version_id: 回滚目标版本标识
        reason: 回滚原因
        status: 回滚状态
        initiated_by: 发起者标识
        completed_at: 完成时间
        error_message: 错误信息
    """

    agent_id: str = ""
    from_version_id: str = ""
    to_version_id: str = ""
    reason: str = ""
    status: RollbackStatus = RollbackStatus.PENDING
    initiated_by: Optional[str] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    error_message: Optional[str] = field(default=None)

    def start(self, operator: Optional[str] = None) -> None:
        """开始回滚操作

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许启动
        """
        if self.status != RollbackStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="ROLLBACK_START_STATUS",
                message=f"回滚当前状态为 {self.status.value}，只有待回滚状态可以启动",
            )
        self.status = RollbackStatus.IN_PROGRESS
        self.initiated_by = operator
        self.touch(operator)

    def complete(self, operator: Optional[str] = None) -> None:
        """完成回滚操作

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许完成
        """
        if self.status != RollbackStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="ROLLBACK_COMPLETE_STATUS",
                message=f"回滚当前状态为 {self.status.value}，只有回滚中状态可以完成",
            )
        self.status = RollbackStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail(self, error: str, operator: Optional[str] = None) -> None:
        """标记回滚操作失败

        Args:
            error: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 回滚状态不允许标记失败
        """
        if self.status != RollbackStatus.IN_PROGRESS:
            raise BusinessRuleViolationException(
                rule="ROLLBACK_FAIL_STATUS",
                message=f"回滚当前状态为 {self.status.value}，只有回滚中状态可以标记失败",
            )
        self.status = RollbackStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)
