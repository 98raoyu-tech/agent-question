"""
Reviewer Agent - 审核结果智能体

负责审核执行结果的质量和正确性，提供改进建议。
"""

from dataclasses import dataclass, field
from typing import Any

from .base import AgentResult, AgentStatus, AgentTask, AgentType, BaseAgent


# ==================== 数据类定义 ====================

@dataclass
class ReviewResult:
    """审核结果数据结构

    Attributes:
        passed: 是否通过审核
        score: 质量评分（0.0 - 1.0）
        issues: 发现的问题列表
        suggestions: 改进建议列表
    """
    passed: bool = False
    score: float = 0.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ==================== Reviewer Agent ====================

class ReviewerAgent(BaseAgent):
    """审核结果智能体

    负责审核执行结果的质量和正确性，提供改进建议。

    Attributes:
        llm_client: LLM 客户端实例
        quality_threshold: 质量阈值（低于此值视为不通过）
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "ReviewerAgent",
        llm_client: Any = None,
        quality_threshold: float = 0.7,
    ) -> None:
        """初始化 Reviewer Agent

        Args:
            agent_id: Agent 唯一标识
            agent_name: Agent 名称
            llm_client: LLM 客户端实例
            quality_threshold: 质量阈值
        """
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=AgentType.REVIEWER,
        )
        self.llm_client = llm_client
        self.quality_threshold = quality_threshold

    # ==================== 核心方法 ====================

    async def execute(self, task: AgentTask) -> AgentResult:
        """审核执行结果

        Args:
            task: 包含待审核结果的任务

        Returns:
            审核结果
        """
        self.status = AgentStatus.RUNNING
        start_time = self._get_current_timestamp()

        try:
            # 提取待审核的输出和需求
            task_output = task.payload.get("output", {})
            requirements = task.payload.get("requirements", [])

            # 步骤1: 审核输出结果
            review_result = await self._review_output(task_output)

            # 步骤2: 验证是否满足需求
            meets_requirements = await self._validate_against_requirements(
                task_output, requirements
            )

            # 步骤3: 提供改进建议
            improvements = await self._suggest_improvements(review_result)

            # 更新审核结果
            review_result.suggestions.extend(improvements)

            # 如果不满足需求，标记为未通过
            if not meets_requirements:
                review_result.passed = False
                review_result.issues.append("输出未满足指定需求")

            # 构建输出结果
            output = {
                "review_result": {
                    "passed": review_result.passed,
                    "score": review_result.score,
                    "issues": review_result.issues,
                    "suggestions": review_result.suggestions,
                },
                "meets_requirements": meets_requirements,
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

    async def _review_output(self, task_output: dict[str, Any]) -> ReviewResult:
        """审核输出结果

        使用 LLM 审核输出结果的质量和正确性。

        Args:
            task_output: 待审核的输出结果

        Returns:
            审核结果
        """
        # TODO: 集成实际的 LLM 审核逻辑
        # 模拟审核结果
        issues: list[str] = []
        score = 0.85

        # 检查输出是否为空
        if not task_output:
            issues.append("输出结果为空")
            score = 0.0

        # 检查输出结构
        if "error" in task_output and task_output["error"]:
            issues.append(f"输出包含错误: {task_output['error']}")
            score *= 0.5

        # 根据阈值判断是否通过
        passed = score >= self.quality_threshold

        return ReviewResult(
            passed=passed,
            score=score,
            issues=issues,
        )

    async def _validate_against_requirements(
        self,
        output: dict[str, Any],
        requirements: list[str],
    ) -> bool:
        """验证是否满足需求

        Args:
            output: 输出结果
            requirements: 需求列表

        Returns:
            是否满足所有需求
        """
        if not requirements:
            return True

        # TODO: 集成实际的需求验证逻辑
        # 模拟验证：检查输出中是否包含需求相关的字段
        output_keys = set(output.keys())
        for requirement in requirements:
            # 简单的需求匹配逻辑
            if requirement.lower() not in str(output_keys).lower():
                return False

        return True

    async def _suggest_improvements(self, review_result: ReviewResult) -> list[str]:
        """提供改进建议

        Args:
            review_result: 审核结果

        Returns:
            改进建议列表
        """
        suggestions: list[str] = []

        # 根据评分提供建议
        if review_result.score < 0.5:
            suggestions.append("输出质量过低，建议重新执行任务")
        elif review_result.score < 0.8:
            suggestions.append("输出质量有待提升，建议优化执行策略")

        # 根据问题提供建议
        for issue in review_result.issues:
            if "错误" in issue:
                suggestions.append("建议检查错误处理逻辑")
            elif "空" in issue:
                suggestions.append("建议检查数据流是否正常")

        return suggestions

    # ==================== 生命周期方法 ====================

    async def pause(self) -> None:
        """暂停 Reviewer Agent"""
        self.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """恢复 Reviewer Agent"""
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
            "quality_threshold": self.quality_threshold,
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
        self.quality_threshold = state.get("quality_threshold", self.quality_threshold)
        self.context = state.get("context", {})

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_current_timestamp() -> float:
        """获取当前时间戳（毫秒）"""
        import time
        return time.time() * 1000