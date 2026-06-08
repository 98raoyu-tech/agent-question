"""
工作流引擎

提供工作流的定义、执行、暂停、恢复和取消等核心功能。
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


# ==================== 枚举定义 ====================

class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ==================== 数据类定义 ====================

@dataclass
class WorkflowStep:
    """工作流步骤定义

    Attributes:
        step_id: 步骤唯一标识
        name: 步骤名称
        agent_type: 执行的Agent类型
        input_mapping: 输入数据映射
        output_mapping: 输出数据映射
        dependencies: 依赖的步骤ID列表
        requires_approval: 是否需要人类审核
    """
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    agent_type: str = ""
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_mapping: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    requires_approval: bool = False


@dataclass
class WorkflowDefinition:
    """工作流定义

    Attributes:
        workflow_id: 工作流唯一标识
        name: 工作流名称
        steps: 工作流步骤列表
        timeout: 超时时间（秒）
        retry_policy: 重试策略
    """
    workflow_id: str = field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    name: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    timeout: int = 3600
    retry_policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """步骤执行结果

    Attributes:
        step_id: 步骤ID
        status: 执行状态
        output: 输出数据
        error: 错误信息
        started_at: 开始时间
        completed_at: 完成时间
        duration_ms: 执行耗时（毫秒）
    """
    step_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


@dataclass
class WorkflowExecution:
    """工作流执行实例

    Attributes:
        execution_id: 执行唯一标识
        workflow_id: 关联的工作流ID
        status: 执行状态
        current_step: 当前执行步骤ID
        step_results: 各步骤执行结果
        started_at: 开始时间
        completed_at: 完成时间
        correlation_id: 关联ID，用于追踪
        input_data: 输入数据
        output_data: 输出数据
    """
    execution_id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:12]}")
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    step_results: dict[str, StepResult] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    correlation_id: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)


# ==================== 工作流引擎 ====================

class WorkflowEngine:
    """工作流引擎

    管理工作流定义和执行，支持工作流的注册、执行、暂停、恢复和取消。

    Attributes:
        workflows: 已注册的工作流定义字典
        executions: 工作流执行实例字典
    """

    def __init__(self) -> None:
        """初始化工作流引擎"""
        self.workflows: dict[str, WorkflowDefinition] = {}
        self.executions: dict[str, WorkflowExecution] = {}

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        """注册工作流定义

        Args:
            definition: 工作流定义

        Raises:
            ValueError: 工作流ID已存在
        """
        if definition.workflow_id in self.workflows:
            raise ValueError(f"工作流ID已存在: {definition.workflow_id}")
        self.workflows[definition.workflow_id] = definition

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        correlation_id: str = "",
    ) -> WorkflowExecution:
        """执行工作流

        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            correlation_id: 关联ID

        Returns:
            工作流执行实例

        Raises:
            ValueError: 工作流不存在
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")

        definition = self.workflows[workflow_id]
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            input_data=input_data,
        )

        self.executions[execution.execution_id] = execution

        # 按依赖顺序执行步骤
        try:
            await self._execute_steps(definition, execution)
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now(timezone.utc)
            execution.output_data["error"] = str(e)

        return execution

    async def _execute_steps(
        self,
        definition: WorkflowDefinition,
        execution: WorkflowExecution,
    ) -> None:
        """按依赖顺序执行所有步骤

        Args:
            definition: 工作流定义
            execution: 执行实例
        """
        completed_steps: set[str] = set()

        while len(completed_steps) < len(definition.steps):
            # 找到可以执行的步骤（所有依赖已完成）
            executable_steps = [
                step for step in definition.steps
                if step.step_id not in completed_steps
                and self._resolve_step_dependencies(step, completed_steps)
            ]

            if not executable_steps:
                raise RuntimeError("检测到循环依赖或无法满足的依赖关系")

            # 并行执行无依赖关系的步骤
            tasks = []
            for step in executable_steps:
                execution.current_step = step.step_id
                tasks.append(self.execute_step(execution.execution_id, step.step_id))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理执行结果
            for step, result in zip(executable_steps, results):
                if isinstance(result, Exception):
                    raise result
                completed_steps.add(step.step_id)

    async def execute_step(
        self,
        execution_id: str,
        step_id: str,
    ) -> StepResult:
        """执行单个步骤

        Args:
            execution_id: 执行ID
            step_id: 步骤ID

        Returns:
            步骤执行结果

        Raises:
            ValueError: 执行或步骤不存在
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        definition = self.workflows[execution.workflow_id]

        # 查找步骤定义
        step_definition = None
        for step in definition.steps:
            if step.step_id == step_id:
                step_definition = step
                break

        if step_definition is None:
            raise ValueError(f"步骤不存在: {step_id}")

        # 创建步骤结果
        result = StepResult(
            step_id=step_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        execution.step_results[step_id] = result

        try:
            # 准备输入数据
            input_data = self._prepare_step_input(step_definition, execution)

            # 执行步骤（这里需要集成具体的Agent执行逻辑）
            # TODO: 集成Agent执行器
            output_data = await self._execute_step_action(step_definition, input_data)

            # 保存输出数据
            result.status = WorkflowStatus.COMPLETED
            result.output = output_data
            result.completed_at = datetime.now(timezone.utc)
            result.duration_ms = (
                result.completed_at - result.started_at
            ).total_seconds() * 1000

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)
            if result.started_at:
                result.duration_ms = (
                    result.completed_at - result.started_at
                ).total_seconds() * 1000
            raise

        return result

    def _prepare_step_input(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> dict[str, Any]:
        """准备步骤输入数据

        根据输入映射从执行上下文中提取数据。

        Args:
            step: 步骤定义
            execution: 执行实例

        Returns:
            步骤输入数据
        """
        input_data: dict[str, Any] = {}

        # 从输入映射中获取数据
        for target_key, source_key in step.input_mapping.items():
            if source_key in execution.input_data:
                input_data[target_key] = execution.input_data[source_key]
            else:
                # 从已完成步骤的输出中查找
                for step_result in execution.step_results.values():
                    if source_key in step_result.output:
                        input_data[target_key] = step_result.output[source_key]
                        break

        return input_data

    async def _execute_step_action(
        self,
        step: WorkflowStep,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """执行步骤具体操作

        Args:
            step: 步骤定义
            input_data: 输入数据

        Returns:
            输出数据

        Note:
            此方法需要在子类中实现具体的执行逻辑
        """
        # 默认实现，返回空结果
        # 子类应该重写此方法以实现具体的Agent调用逻辑
        return {"step_id": step.step_id, "status": "completed"}

    async def pause_workflow(self, execution_id: str) -> None:
        """暂停工作流

        Args:
            execution_id: 执行ID

        Raises:
            ValueError: 执行不存在或状态不允许暂停
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        if execution.status != WorkflowStatus.RUNNING:
            raise ValueError(f"执行状态不允许暂停: {execution.status.value}")

        execution.status = WorkflowStatus.PAUSED

    async def resume_workflow(self, execution_id: str) -> None:
        """恢复工作流

        Args:
            execution_id: 执行ID

        Raises:
            ValueError: 执行不存在或状态不允许恢复
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        if execution.status != WorkflowStatus.PAUSED:
            raise ValueError(f"执行状态不允许恢复: {execution.status.value}")

        execution.status = WorkflowStatus.RUNNING

        # 从当前步骤继续执行
        definition = self.workflows[execution.workflow_id]
        await self._execute_steps(definition, execution)

    async def cancel_workflow(self, execution_id: str) -> None:
        """取消工作流

        Args:
            execution_id: 执行ID

        Raises:
            ValueError: 执行不存在或状态不允许取消
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        execution = self.executions[execution_id]
        if execution.status not in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            raise ValueError(f"执行状态不允许取消: {execution.status.value}")

        execution.status = WorkflowStatus.FAILED
        execution.completed_at = datetime.now(timezone.utc)
        execution.output_data["cancelled"] = True

    def get_execution_status(self, execution_id: str) -> WorkflowExecution:
        """获取执行状态

        Args:
            execution_id: 执行ID

        Returns:
            执行实例

        Raises:
            ValueError: 执行不存在
        """
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")

        return self.executions[execution_id]

    def _resolve_step_dependencies(
        self,
        step: WorkflowStep,
        completed_steps: set[str],
    ) -> bool:
        """检查步骤依赖是否满足

        Args:
            step: 步骤定义
            completed_steps: 已完成的步骤ID集合

        Returns:
            依赖是否满足
        """
        return all(dep in completed_steps for dep in step.dependencies)