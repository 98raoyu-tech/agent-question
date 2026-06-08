"""
评估门控领域事件

定义评估门控相关的领域事件，用于事件溯源和跨模块通信。
"""

from dataclasses import dataclass

from ...common.base_event import BaseEvent
from .enums import EvaluationTargetType


@dataclass
class EvaluationGateEvent(BaseEvent):
    """评估门控领域事件

    记录门控评估结果的领域事件，支持事件驱动架构下的跨模块通知。

    Attributes:
        gate_id: 门控标识
        target_id: 评估目标标识
        target_type: 评估目标类型
        passed: 是否通过
        score: 综合评分
    """

    gate_id: str = ""
    target_id: str = ""
    target_type: EvaluationTargetType = EvaluationTargetType.AGENT
    passed: bool = False
    score: float = 0.0
