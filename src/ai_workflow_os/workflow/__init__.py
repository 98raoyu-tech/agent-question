"""
工作流模块

提供工作流引擎、Temporal集成、Saga模式回滚和人类审核等功能。
"""

from .engine import (
    WorkflowEngine,
    WorkflowStatus,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    StepResult,
)
from .temporal import TemporalWorkflowEngine
from .saga import SagaOrchestrator, SagaStep, SagaExecution
from .human_approval import HumanApprovalManager, ApprovalRequest, ApprovalStatus


# ==================== 导出列表 ====================

__all__ = [
    # 工作流引擎
    "WorkflowEngine",
    "WorkflowStatus",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowExecution",
    "StepResult",

    # Temporal集成
    "TemporalWorkflowEngine",

    # Saga模式
    "SagaOrchestrator",
    "SagaStep",
    "SagaExecution",

    # 人类审核
    "HumanApprovalManager",
    "ApprovalRequest",
    "ApprovalStatus",
]