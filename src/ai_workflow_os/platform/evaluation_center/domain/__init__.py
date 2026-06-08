"""
评估中心领域层

定义评测数据集、运行和评分相关的领域实体和枚举。
"""

from .enums import MetricType, RunStatus
from .evaluation_dataset import EvaluationDataset
from .evaluation_run import EvaluationRun
from .evaluation_score import EvaluationScore
