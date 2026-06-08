"""
评估中心枚举定义

定义评测指标类型和运行状态等枚举。
"""

from enum import Enum


class MetricType(str, Enum):
    """评测指标类型枚举"""

    ACCURACY = "accuracy"
    """准确率"""

    LATENCY = "latency"
    """延迟"""

    COST = "cost"
    """成本"""

    HALLUCINATION = "hallucination"
    """幻觉率"""

    RELEVANCE = "relevance"
    """相关性"""

    FAITHFULNESS = "faithfulness"
    """忠实度"""

    COMPLETENESS = "completeness"
    """完整性"""

    SAFETY = "safety"
    """安全性"""


class RunStatus(str, Enum):
    """评测运行状态枚举"""

    PENDING = "pending"
    """待运行"""

    RUNNING = "running"
    """运行中"""

    COMPLETED = "completed"
    """运行完成"""

    FAILED = "failed"
    """运行失败"""

    CANCELLED = "cancelled"
    """已取消"""
