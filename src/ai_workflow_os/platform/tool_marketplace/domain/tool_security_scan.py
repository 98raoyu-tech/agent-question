"""
工具安全扫描实体

管理工具的安全扫描流程和漏洞报告。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class ScanType(str, Enum):
    """扫描类型枚举"""

    STATIC = "static"
    DYNAMIC = "dynamic"
    DEPENDENCY = "dependency"


class ScanStatus(str, Enum):
    """扫描状态枚举"""

    PENDING = "pending"
    SCANNING = "scanning"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class ToolSecurityScan(BaseEntity):
    """工具安全扫描实体

    记录工具版本的安全扫描结果和漏洞详情。

    Attributes:
        tool_id: 关联的工具标识
        version_id: 关联的版本标识
        scan_type: 扫描类型
        status: 扫描状态
        severity_counts: 各严重等级漏洞计数
        vulnerabilities: 漏洞详情列表
        scan_started_at: 扫描开始时间
        scan_completed_at: 扫描完成时间
        passed: 是否通过扫描
    """

    tool_id: str = ""
    version_id: str = ""
    scan_type: ScanType = ScanType.STATIC
    status: ScanStatus = ScanStatus.PENDING
    severity_counts: dict[str, int] = field(default_factory=dict)
    vulnerabilities: list[dict] = field(default_factory=list)
    scan_started_at: Optional[datetime] = field(default=None)
    scan_completed_at: Optional[datetime] = field(default=None)
    passed: bool = False

    def start_scan(self, operator: Optional[str] = None) -> None:
        """开始安全扫描

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 扫描状态不允许该操作
        """
        if self.status != ScanStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="SCAN_STATUS_TRANSITION",
                message=f"扫描 [{self.id}] 当前状态为 {self.status.value}，不允许重新启动",
            )
        self.status = ScanStatus.SCANNING
        self.scan_started_at = datetime.now(timezone.utc)
        self.touch(operator)

    def complete_scan(
        self,
        vulnerabilities: list[dict],
        operator: Optional[str] = None,
    ) -> None:
        """完成安全扫描

        Args:
            vulnerabilities: 漏洞详情列表
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 扫描状态不允许该操作
        """
        if self.status != ScanStatus.SCANNING:
            raise BusinessRuleViolationException(
                rule="SCAN_STATUS_TRANSITION",
                message=f"扫描 [{self.id}] 当前状态为 {self.status.value}，不允许完成操作",
            )
        self.vulnerabilities = vulnerabilities
        self.severity_counts = self._count_severities(vulnerabilities)
        has_critical = self.severity_counts.get("critical", 0) > 0
        has_high = self.severity_counts.get("high", 0) > 0
        self.passed = not (has_critical or has_high)
        self.status = ScanStatus.PASSED if self.passed else ScanStatus.FAILED
        self.scan_completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail_scan(
        self,
        error: str,
        operator: Optional[str] = None,
    ) -> None:
        """扫描失败

        Args:
            error: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 扫描状态不允许该操作
        """
        if self.status != ScanStatus.SCANNING:
            raise BusinessRuleViolationException(
                rule="SCAN_STATUS_TRANSITION",
                message=f"扫描 [{self.id}] 当前状态为 {self.status.value}，不允许失败操作",
            )
        self.status = ScanStatus.FAILED
        self.passed = False
        self.vulnerabilities = [{"type": "scan_error", "message": error}]
        self.scan_completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def _count_severities(self, vulnerabilities: list[dict]) -> dict[str, int]:
        """统计各严重等级的漏洞数量

        Args:
            vulnerabilities: 漏洞详情列表

        Returns:
            各等级漏洞计数
        """
        counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
        return counts
