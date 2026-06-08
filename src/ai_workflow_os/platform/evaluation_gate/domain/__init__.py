"""
评估门控领域层

定义质量门控、评估报告相关的领域实体、枚举和领域事件。
"""

from .enums import EvaluationTargetType, GateStatus, MetricType
from .evaluation_gate_event import EvaluationGateEvent
from .evaluation_report import EvaluationReport
from .quality_gate import QualityGate
