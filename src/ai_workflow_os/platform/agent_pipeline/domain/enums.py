"""
Agent Pipeline 枚举定义

定义流水线阶段、状态和步骤状态等枚举类型。
"""

from enum import Enum


class PipelineStage(str, Enum):
    """流水线阶段枚举

    定义Agent发布流水线的完整阶段序列。
    """

    CREATE = "create"
    """创建阶段"""

    TEST = "test"
    """测试阶段"""

    EVALUATION = "evaluation"
    """评估阶段"""

    APPROVAL = "approval"
    """审批阶段"""

    RELEASE = "release"
    """发布阶段"""

    DEPLOY = "deploy"
    """部署阶段"""

    OBSERVE = "observe"
    """观测阶段"""

    ROLLBACK = "rollback"
    """回滚阶段"""


# 流水线阶段的有序序列
PIPELINE_STAGE_ORDER: list[PipelineStage] = [
    PipelineStage.CREATE,
    PipelineStage.TEST,
    PipelineStage.EVALUATION,
    PipelineStage.APPROVAL,
    PipelineStage.RELEASE,
    PipelineStage.DEPLOY,
    PipelineStage.OBSERVE,
]


class PipelineStatus(str, Enum):
    """流水线状态枚举"""

    PENDING = "pending"
    """待启动"""

    RUNNING = "running"
    """运行中"""

    PASSED = "passed"
    """通过"""

    FAILED = "failed"
    """失败"""

    CANCELLED = "cancelled"
    """已取消"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


class PipelineStepStatus(str, Enum):
    """流水线步骤状态枚举"""

    PENDING = "pending"
    """待执行"""

    RUNNING = "running"
    """执行中"""

    PASSED = "passed"
    """通过"""

    FAILED = "failed"
    """失败"""

    SKIPPED = "skipped"
    """跳过"""

    BLOCKED = "blocked"
    """阻断"""
