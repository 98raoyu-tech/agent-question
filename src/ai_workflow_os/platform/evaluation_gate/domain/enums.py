"""
评估门控枚举定义

定义评估目标类型、门控状态和评测指标类型等枚举。
"""

from enum import Enum


class EvaluationTargetType(str, Enum):
    """评估目标类型枚举"""

    AGENT = "agent"
    """Agent"""

    WORKFLOW = "workflow"
    """工作流"""

    PROMPT = "prompt"
    """Prompt模板"""

    KNOWLEDGE = "knowledge"
    """知识库"""


class GateStatus(str, Enum):
    """门控状态枚举"""

    PENDING = "pending"
    """待评估"""

    EVALUATING = "evaluating"
    """评估中"""

    PASSED = "passed"
    """通过"""

    FAILED = "failed"
    """未通过"""

    WAIVED = "waived"
    """已豁免"""

    EXPIRED = "expired"
    """已过期"""


class MetricType(str, Enum):
    """评测指标类型枚举"""

    ACCURACY = "accuracy"
    """准确率"""

    LATENCY = "latency"
    """延迟"""

    COST = "cost"
    """成本"""

    SUCCESS_RATE = "success_rate"
    """成功率"""

    HALLUCINATION = "hallucination"
    """幻觉率"""

    GROUNDEDNESS = "groundedness"
    """事实依据性"""

    SAFETY = "safety"
    """安全性"""

    COMPLETENESS = "completeness"
    """完整性"""

    RELEVANCE = "relevance"
    """相关性"""
