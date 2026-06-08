"""
Agent测试运行实体

记录Agent版本的测试执行情况，支持多种测试类型和生命周期管理。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import TestRunStatus, TestType


@dataclass
class AgentTestRun(BaseEntity):
    """Agent测试运行实体

    记录一次测试运行的完整信息，包括测试状态、通过率和结果。

    Attributes:
        agent_id: 关联的Agent标识
        version_id: 关联的版本标识
        test_name: 测试名称
        status: 测试运行状态
        test_type: 测试类型
        started_at: 开始时间
        completed_at: 完成时间
        error_message: 错误信息
        results: 测试结果详情
        pass_rate: 通过率（0.0 ~ 1.0）
    """

    agent_id: str = ""
    version_id: str = ""
    test_name: str = ""
    status: TestRunStatus = TestRunStatus.PENDING
    test_type: TestType = TestType.UNIT
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    error_message: Optional[str] = field(default=None)
    results: dict[str, Any] = field(default_factory=dict)
    pass_rate: float = 0.0

    def start(self, operator: Optional[str] = None) -> None:
        """开始测试运行

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许启动
        """
        if self.status != TestRunStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="TEST_RUN_START_STATUS",
                message=f"测试当前状态为 {self.status.value}，只有待运行状态可以启动",
            )
        self.status = TestRunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.touch(operator)

    def complete(
        self,
        pass_rate: float,
        operator: Optional[str] = None,
    ) -> None:
        """完成测试运行

        Args:
            pass_rate: 通过率（0.0 ~ 1.0）
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许完成
        """
        if self.status != TestRunStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="TEST_RUN_COMPLETE_STATUS",
                message=f"测试当前状态为 {self.status.value}，只有运行中状态可以完成",
            )
        self.status = TestRunStatus.PASSED if pass_rate >= 1.0 else TestRunStatus.FAILED
        self.pass_rate = pass_rate
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail(self, error: str, operator: Optional[str] = None) -> None:
        """标记测试运行失败

        Args:
            error: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许标记失败
        """
        if self.status != TestRunStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="TEST_RUN_FAIL_STATUS",
                message=f"测试当前状态为 {self.status.value}，只有运行中状态可以标记失败",
            )
        self.status = TestRunStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)
