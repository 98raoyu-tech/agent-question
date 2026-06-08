"""
评分实体

定义评测评分的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import MetricType


@dataclass
class EvaluationScore(BaseEntity):
    """评测评分实体

    记录单个测试用例在某个指标上的评分结果。

    Attributes:
        run_id: 关联的运行标识
        dataset_id: 关联的数据集标识
        test_case_index: 测试用例索引
        metric_type: 指标类型
        score: 评分值
        expected_output: 期望输出
        actual_output: 实际输出
        latency_ms: 延迟（毫秒）
        token_usage: Token使用量
        cost: 成本
        details: 详细信息
    """

    run_id: str = ""
    dataset_id: str = ""
    test_case_index: int = 0
    metric_type: MetricType = MetricType.ACCURACY
    score: float = 0.0
    expected_output: str = ""
    actual_output: str = ""
    latency_ms: float = 0.0
    token_usage: int = 0
    cost: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def is_passing(self, threshold: float = 0.8) -> bool:
        """判断是否通过阈值

        Args:
            threshold: 通过阈值

        Returns:
            是否通过
        """
        return self.score >= threshold
