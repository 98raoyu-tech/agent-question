"""
Prompt基准测试实体

管理Prompt模板版本的性能基准测试。
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException


class BenchmarkStatus(str, Enum):
    """基准测试状态枚举"""

    PENDING = "pending"
    """待运行"""

    RUNNING = "running"
    """运行中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """运行失败"""


@dataclass
class PromptBenchmark(BaseEntity):
    """Prompt基准测试实体

    管理Prompt模板版本的性能基准测试，包括评分、延迟和成本统计。

    Attributes:
        prompt_id: 关联的Prompt模板标识
        version_id: 关联的版本标识
        benchmark_name: 基准测试名称
        test_cases: 测试用例列表
        status: 测试状态
        avg_score: 平均评分
        avg_latency_ms: 平均延迟（毫秒）
        avg_cost: 平均成本
        total_tokens: 总Token数
        results: 测试结果列表
        completed_at: 完成时间
    """

    prompt_id: str = ""
    version_id: str = ""
    benchmark_name: str = ""
    test_cases: list[dict[str, Any]] = field(default_factory=list)
    status: BenchmarkStatus = BenchmarkStatus.PENDING
    avg_score: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost: float = 0.0
    total_tokens: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    completed_at: datetime | None = field(default=None)

    async def run(
        self,
        test_executor: Callable[..., Coroutine[Any, Any, list[dict[str, Any]]]],
        operator: str | None = None,
    ) -> None:
        """运行基准测试

        Args:
            test_executor: 测试执行器函数
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许运行
        """
        if self.status not in (BenchmarkStatus.PENDING, BenchmarkStatus.FAILED):
            raise BusinessRuleViolationException(
                rule="benchmark_run",
                message=f"基准测试当前状态为{self.status.value}，无法运行",
            )

        if not self.test_cases:
            raise BusinessRuleViolationException(
                rule="benchmark_run",
                message="测试用例不能为空",
            )

        self.status = BenchmarkStatus.RUNNING
        self.touch(operator)

        try:
            results = await test_executor(self.test_cases)
            self.complete(results, operator)
        except Exception as error:
            self.fail(str(error), operator)
            raise

    def complete(
        self,
        results: list[dict[str, Any]],
        operator: str | None = None,
    ) -> None:
        """完成基准测试

        Args:
            results: 测试结果列表
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许完成
        """
        if self.status != BenchmarkStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="benchmark_complete",
                message=f"基准测试当前状态为{self.status.value}，无法完成",
            )

        self.results = results
        self.status = BenchmarkStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

        if results:
            scores = [r.get("score", 0) for r in results if "score" in r]
            latencies = [r.get("latency_ms", 0) for r in results if "latency_ms" in r]
            costs = [r.get("cost", 0) for r in results if "cost" in r]
            tokens = [r.get("tokens", 0) for r in results if "tokens" in r]

            self.avg_score = sum(scores) / len(scores) if scores else 0.0
            self.avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
            self.avg_cost = sum(costs) / len(costs) if costs else 0.0
            self.total_tokens = sum(tokens)

        self.touch(operator)

    def fail(self, error: str, operator: str | None = None) -> None:
        """标记基准测试失败

        Args:
            error: 错误信息
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: 测试状态不允许失败
        """
        if self.status != BenchmarkStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="benchmark_fail",
                message=f"基准测试当前状态为{self.status.value}，无法标记为失败",
            )

        self.status = BenchmarkStatus.FAILED
        self.results = [{"error": error}]
        self.completed_at = datetime.now(UTC)
        self.touch(operator)
