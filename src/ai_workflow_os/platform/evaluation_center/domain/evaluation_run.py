"""
评测运行实体

定义评测运行的核心业务实体。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import RunStatus


@dataclass
class EvaluationRun(BaseEntity):
    """评测运行实体

    记录一次评测运行的完整信息。

    Attributes:
        dataset_id: 关联的数据集标识
        agent_id: 关联的Agent标识
        run_name: 运行名称
        status: 运行状态
        total_cases: 总测试用例数
        completed_cases: 已完成用例数
        failed_cases: 失败用例数
        started_at: 开始时间
        completed_at: 完成时间
        error_message: 错误信息
        config: 运行配置
        metadata: 扩展元数据
    """

    dataset_id: str = ""
    agent_id: str = ""
    run_name: str = ""
    status: RunStatus = RunStatus.PENDING
    total_cases: int = 0
    completed_cases: int = 0
    failed_cases: int = 0
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    error_message: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self, operator: Optional[str] = None) -> None:
        """开始运行

        Args:
            operator: 操作者标识
        """
        from datetime import timezone

        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.touch(operator)

    def complete(self, operator: Optional[str] = None) -> None:
        """完成运行

        Args:
            operator: 操作者标识
        """
        from datetime import timezone

        self.status = RunStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.touch(operator)

    def fail(self, error: str = "", operator: Optional[str] = None) -> None:
        """运行失败

        Args:
            error: 错误信息
            operator: 操作者标识
        """
        from datetime import timezone

        self.status = RunStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error
        self.touch(operator)

    def cancel(self, operator: Optional[str] = None) -> None:
        """取消运行

        Args:
            operator: 操作者标识
        """
        self.status = RunStatus.CANCELLED
        self.touch(operator)

    def increment_completed(self, operator: Optional[str] = None) -> None:
        """增加已完成用例数

        Args:
            operator: 操作者标识
        """
        self.completed_cases += 1
        self.touch(operator)

    def increment_failed(self, operator: Optional[str] = None) -> None:
        """增加失败用例数

        Args:
            operator: 操作者标识
        """
        self.failed_cases += 1
        self.touch(operator)

    @property
    def progress(self) -> float:
        """计算运行进度

        Returns:
            运行进度百分比（0-100）
        """
        if self.total_cases == 0:
            return 0.0
        return (self.completed_cases + self.failed_cases) / self.total_cases * 100

    @property
    def success_rate(self) -> float:
        """计算成功率

        Returns:
            成功率百分比（0-100）
        """
        processed = self.completed_cases + self.failed_cases
        if processed == 0:
            return 0.0
        return self.completed_cases / processed * 100
