"""
Planner Agent - 任务规划智能体

负责接收用户请求，使用 LLM 进行任务拆解，生成执行计划。
"""

from dataclasses import dataclass, field
from typing import Any

from .base import AgentResult, AgentStatus, AgentTask, AgentType, BaseAgent


# ==================== 数据类定义 ====================

@dataclass
class SubTask:
    """子任务数据结构

    Attributes:
        task_id: 子任务唯一标识
        description: 子任务描述
        dependencies: 依赖的子任务 ID 列表
        estimated_duration: 预估执行时长（秒）
        required_tools: 所需工具列表
    """
    task_id: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    estimated_duration: int = 0
    required_tools: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """执行计划数据结构

    Attributes:
        plan_id: 计划唯一标识
        sub_tasks: 子任务列表
        total_estimated_time: 总预估时长（秒）
        requires_human_approval: 是否需要人工审批
    """
    plan_id: str = ""
    sub_tasks: list[SubTask] = field(default_factory=list)
    total_estimated_time: int = 0
    requires_human_approval: bool = False


# ==================== Planner Agent ====================

class PlannerAgent(BaseAgent):
    """任务规划智能体

    负责将用户请求拆解为可执行的子任务，并生成执行计划。

    Attributes:
        llm_client: LLM 客户端实例
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "PlannerAgent",
        llm_client: Any = None,
    ) -> None:
        """初始化 Planner Agent

        Args:
            agent_id: Agent 唯一标识
            agent_name: Agent 名称
            llm_client: LLM 客户端实例
        """
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=AgentType.PLANNER,
        )
        self.llm_client = llm_client

    # ==================== 核心方法 ====================

    async def execute(self, task: AgentTask) -> AgentResult:
        """执行任务规划

        接收用户请求，使用 LLM 进行任务拆解，生成执行计划。

        Args:
            task: 待执行的任务

        Returns:
            包含执行计划的执行结果
        """
        self.status = AgentStatus.RUNNING
        start_time = self._get_current_timestamp()

        try:
            # 提取用户请求
            user_prompt = task.payload.get("prompt", "")

            # 步骤1: 拆解任务为子任务列表
            sub_tasks = await self._decompose_task(user_prompt)

            # 步骤2: 创建执行计划
            execution_plan = await self._create_execution_plan(sub_tasks)

            # 步骤3: 评估整体复杂度
            complexity = await self._estimate_complexity(task)

            # 构建输出结果
            output = {
                "execution_plan": {
                    "plan_id": execution_plan.plan_id,
                    "sub_tasks": [
                        {
                            "task_id": st.task_id,
                            "description": st.description,
                            "dependencies": st.dependencies,
                            "estimated_duration": st.estimated_duration,
                            "required_tools": st.required_tools,
                        }
                        for st in execution_plan.sub_tasks
                    ],
                    "total_estimated_time": execution_plan.total_estimated_time,
                    "requires_human_approval": execution_plan.requires_human_approval,
                },
                "complexity": complexity,
            }

            duration_ms = self._get_current_timestamp() - start_time
            self.status = AgentStatus.COMPLETED

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED.value,
                output=output,
                duration_ms=duration_ms,
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            duration_ms = self._get_current_timestamp() - start_time

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status=AgentStatus.FAILED.value,
                error=str(e),
                duration_ms=duration_ms,
            )

    # ==================== 内部方法 ====================

    async def _decompose_task(self, prompt: str) -> list[SubTask]:
        """拆解任务为子任务列表

        使用 LLM 将用户请求拆解为可执行的子任务。

        Args:
            prompt: 用户请求文本

        Returns:
            子任务列表
        """
        # TODO: 集成实际的 LLM 调用
        # 模拟 LLM 返回的子任务拆解结果
        sub_tasks = [
            SubTask(
                task_id="sub_task_001",
                description="分析用户需求",
                dependencies=[],
                estimated_duration=30,
                required_tools=["text_analyzer"],
            ),
            SubTask(
                task_id="sub_task_002",
                description="检索相关知识库",
                dependencies=["sub_task_001"],
                estimated_duration=60,
                required_tools=["knowledge_retriever"],
            ),
            SubTask(
                task_id="sub_task_003",
                description="生成执行方案",
                dependencies=["sub_task_002"],
                estimated_duration=90,
                required_tools=["code_generator"],
            ),
        ]
        return sub_tasks

    async def _create_execution_plan(self, sub_tasks: list[SubTask]) -> ExecutionPlan:
        """创建执行计划

        根据子任务列表确定执行顺序和依赖关系。

        Args:
            sub_tasks: 子任务列表

        Returns:
            执行计划
        """
        import uuid

        # 计算总预估时长
        total_time = sum(st.estimated_duration for st in sub_tasks)

        # 判断是否需要人工审批（复杂任务需要审批）
        requires_approval = total_time > 300

        plan = ExecutionPlan(
            plan_id=uuid.uuid4().hex[:12],
            sub_tasks=sub_tasks,
            total_estimated_time=total_time,
            requires_human_approval=requires_approval,
        )
        return plan

    async def _estimate_complexity(self, task: AgentTask) -> int:
        """评估任务复杂度

        根据任务内容评估复杂度等级（1-10）。

        Args:
            task: 待评估的任务

        Returns:
            复杂度等级（1-10）
        """
        # 基于任务负载大小和类型进行复杂度评估
        payload_size = len(str(task.payload))
        task_type_complexity = {
            "simple_query": 2,
            "data_analysis": 5,
            "code_generation": 7,
            "system_design": 9,
        }
        base_complexity = task_type_complexity.get(task.task_type, 5)

        # 根据负载大小调整复杂度
        if payload_size > 1000:
            base_complexity = min(base_complexity + 2, 10)

        return base_complexity

    # ==================== 生命周期方法 ====================

    async def pause(self) -> None:
        """暂停 Planner Agent"""
        self.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """恢复 Planner Agent"""
        self.status = AgentStatus.IDLE

    async def checkpoint(self) -> dict[str, Any]:
        """保存检查点

        Returns:
            检查点状态数据
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "context": self.context,
        }

    async def restore(self, state: dict[str, Any]) -> None:
        """从检查点恢复状态

        Args:
            state: 检查点状态数据
        """
        self.agent_id = state.get("agent_id", self.agent_id)
        self.agent_name = state.get("agent_name", self.agent_name)
        self.status = AgentStatus(state.get("status", AgentStatus.IDLE.value))
        self.context = state.get("context", {})

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_current_timestamp() -> float:
        """获取当前时间戳（毫秒）"""
        import time
        return time.time() * 1000