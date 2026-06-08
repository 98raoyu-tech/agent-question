"""
Agent Lifecycle枚举定义

定义Agent生命周期管理相关的枚举类型，包括生命周期状态、审批状态、部署策略，
以及严格的状态机转换规则。
"""

from enum import Enum


class AgentLifecycleState(str, Enum):
    """Agent生命周期状态枚举"""

    DRAFT = "draft"
    """草稿"""

    TESTING = "testing"
    """测试中"""

    EVALUATION = "evaluation"
    """评估中"""

    APPROVAL = "approval"
    """审批中"""

    RELEASED = "released"
    """已发布"""

    DEPLOYED = "deployed"
    """已部署"""

    OBSERVING = "observing"
    """观测中"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


class ApprovalStatus(str, Enum):
    """审批状态枚举"""

    PENDING = "pending"
    """待审批"""

    APPROVED = "approved"
    """已批准"""

    REJECTED = "rejected"
    """已拒绝"""

    ESCALATED = "escalated"
    """已升级"""


class DeploymentStrategy(str, Enum):
    """部署策略枚举"""

    CANARY = "canary"
    """金丝雀发布"""

    BLUE_GREEN = "blue_green"
    """蓝绿部署"""

    ROLLING = "rolling"
    """滚动更新"""

    DIRECT = "direct"
    """直接部署"""


class TestRunStatus(str, Enum):
    """测试运行状态枚举"""

    PENDING = "pending"
    """待运行"""

    RUNNING = "running"
    """运行中"""

    PASSED = "passed"
    """通过"""

    FAILED = "failed"
    """失败"""

    SKIPPED = "skipped"
    """跳过"""


class TestType(str, Enum):
    """测试类型枚举"""

    UNIT = "unit"
    """单元测试"""

    INTEGRATION = "integration"
    """集成测试"""

    E2E = "e2e"
    """端到端测试"""

    REGRESSION = "regression"
    """回归测试"""


class EvaluationStatus(str, Enum):
    """评估状态枚举"""

    PENDING = "pending"
    """待评估"""

    RUNNING = "running"
    """评估中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """失败"""


class DeploymentStatus(str, Enum):
    """部署状态枚举"""

    PENDING = "pending"
    """待部署"""

    DEPLOYING = "deploying"
    """部署中"""

    ACTIVE = "active"
    """运行中"""

    FAILED = "failed"
    """失败"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


class DeploymentEnvironment(str, Enum):
    """部署环境枚举"""

    DEV = "dev"
    """开发环境"""

    TEST = "test"
    """测试环境"""

    STAGING = "staging"
    """预发布环境"""

    PROD = "prod"
    """生产环境"""


class RollbackStatus(str, Enum):
    """回滚状态枚举"""

    PENDING = "pending"
    """待回滚"""

    IN_PROGRESS = "in_progress"
    """回滚中"""

    COMPLETED = "completed"
    """已完成"""

    FAILED = "failed"
    """失败"""


VALID_TRANSITIONS: dict[AgentLifecycleState, list[AgentLifecycleState]] = {
    AgentLifecycleState.DRAFT: [AgentLifecycleState.TESTING],
    AgentLifecycleState.TESTING: [AgentLifecycleState.EVALUATION, AgentLifecycleState.DRAFT],
    AgentLifecycleState.EVALUATION: [AgentLifecycleState.APPROVAL, AgentLifecycleState.DRAFT],
    AgentLifecycleState.APPROVAL: [AgentLifecycleState.RELEASED, AgentLifecycleState.DRAFT],
    AgentLifecycleState.RELEASED: [AgentLifecycleState.DEPLOYED],
    AgentLifecycleState.DEPLOYED: [AgentLifecycleState.OBSERVING, AgentLifecycleState.ROLLED_BACK],
    AgentLifecycleState.OBSERVING: [AgentLifecycleState.ROLLED_BACK, AgentLifecycleState.DEPLOYED],
    AgentLifecycleState.ROLLED_BACK: [AgentLifecycleState.DRAFT],
}
