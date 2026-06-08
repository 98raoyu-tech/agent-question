"""
Agent Lifecycle领域层

定义Agent生命周期管理相关的领域实体、值对象和枚举。
"""

from .agent_approval import AgentApproval
from .agent_definition import AgentLifecycleDefinition
from .agent_deployment import AgentDeployment
from .agent_evaluation import AgentEvaluation
from .agent_rollback import AgentRollback
from .agent_test_run import AgentTestRun
from .agent_version import AgentLifecycleVersion
from .enums import (
    AgentLifecycleState,
    ApprovalStatus,
    DeploymentEnvironment,
    DeploymentStatus,
    DeploymentStrategy,
    EvaluationStatus,
    RollbackStatus,
    TestRunStatus,
    TestType,
    VALID_TRANSITIONS,
)
