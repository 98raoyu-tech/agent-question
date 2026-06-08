"""
Policy Agent - 风险控制智能体

负责评估操作的风险等级，检查策略合规性，判断是否需要人类审核。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import AgentResult, AgentStatus, AgentTask, AgentType, BaseAgent


# ==================== 枚举定义 ====================

class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==================== 数据类定义 ====================

@dataclass
class PolicyCheckResult:
    """策略检查结果数据结构

    Attributes:
        compliant: 是否合规
        risk_level: 风险等级
        violations: 违规项列表
        requires_approval: 是否需要审批
    """
    compliant: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    violations: list[str] = field(default_factory=list)
    requires_approval: bool = False


# ==================== Policy Agent ====================

class PolicyAgent(BaseAgent):
    """风险控制智能体

    负责评估操作风险，检查策略合规性，保障系统安全。

    Attributes:
        policy_engine: 策略引擎实例
        risk_thresholds: 风险阈值配置
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "PolicyAgent",
        policy_engine: Any = None,
    ) -> None:
        """初始化 Policy Agent

        Args:
            agent_id: Agent 唯一标识
            agent_name: Agent 名称
            policy_engine: 策略引擎实例
        """
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=AgentType.POLICY,
        )
        self.policy_engine = policy_engine

        # 风险阈值配置：不同风险等级对应的审批要求
        self.risk_thresholds: dict[RiskLevel, bool] = {
            RiskLevel.LOW: False,
            RiskLevel.MEDIUM: False,
            RiskLevel.HIGH: True,
            RiskLevel.CRITICAL: True,
        }

    # ==================== 核心方法 ====================

    async def execute(self, task: AgentTask) -> AgentResult:
        """评估操作的风险等级

        Args:
            task: 包含待评估操作的任务

        Returns:
            策略检查结果
        """
        self.status = AgentStatus.RUNNING
        start_time = self._get_current_timestamp()

        try:
            # 提取待评估的操作
            action = task.payload.get("action", {})
            agent_id = task.payload.get("agent_id", "")

            # 步骤1: 评估风险等级
            risk_level = await self._evaluate_risk(action)

            # 步骤2: 检查策略合规性
            is_compliant = await self._check_policy_compliance(action)

            # 步骤3: 判断是否需要人类审核
            requires_approval = await self._require_human_approval(risk_level)

            # 收集违规项
            violations: list[str] = []
            if not is_compliant:
                violations.append(f"操作不符合策略要求: {action.get('type', 'unknown')}")

            # 构建检查结果
            check_result = PolicyCheckResult(
                compliant=is_compliant,
                risk_level=risk_level,
                violations=violations,
                requires_approval=requires_approval,
            )

            # 构建输出结果
            output = {
                "policy_check_result": {
                    "compliant": check_result.compliant,
                    "risk_level": check_result.risk_level.value,
                    "violations": check_result.violations,
                    "requires_approval": check_result.requires_approval,
                },
                "agent_id": agent_id,
                "action_type": action.get("type", "unknown"),
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

    async def _evaluate_risk(self, action: dict[str, Any]) -> RiskLevel:
        """评估风险等级

        根据操作类型和内容评估风险等级。

        Args:
            action: 待评估的操作

        Returns:
            风险等级
        """
        # TODO: 集成实际的策略引擎
        if self.policy_engine:
            return await self.policy_engine.evaluate_risk(action)

        # 基于操作类型的风险评估逻辑
        action_type = action.get("type", "")
        risk_mapping: dict[str, RiskLevel] = {
            "read": RiskLevel.LOW,
            "query": RiskLevel.LOW,
            "write": RiskLevel.MEDIUM,
            "update": RiskLevel.MEDIUM,
            "delete": RiskLevel.HIGH,
            "deploy": RiskLevel.HIGH,
            "admin": RiskLevel.CRITICAL,
        }

        return risk_mapping.get(action_type, RiskLevel.MEDIUM)

    async def _check_policy_compliance(self, action: dict[str, Any]) -> bool:
        """检查策略合规性

        验证操作是否符合系统策略要求。

        Args:
            action: 待检查的操作

        Returns:
            是否合规
        """
        # TODO: 集成实际的策略引擎
        if self.policy_engine:
            return await self.policy_engine.check_compliance(action)

        # 基本合规性检查逻辑
        action_type = action.get("type", "")

        # 检查是否包含必需字段
        if not action_type:
            return False

        # 检查操作是否在允许范围内
        allowed_actions = {"read", "query", "write", "update", "delete", "deploy"}
        if action_type not in allowed_actions:
            return False

        return True

    async def _require_human_approval(self, risk_level: RiskLevel) -> bool:
        """判断是否需要人类审核

        Args:
            risk_level: 风险等级

        Returns:
            是否需要人类审核
        """
        return self.risk_thresholds.get(risk_level, True)

    # ==================== 生命周期方法 ====================

    async def pause(self) -> None:
        """暂停 Policy Agent"""
        self.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """恢复 Policy Agent"""
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
            "risk_thresholds": {k.value: v for k, v in self.risk_thresholds.items()},
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

        # 恢复风险阈值配置
        thresholds = state.get("risk_thresholds", {})
        for level_str, required in thresholds.items():
            try:
                level = RiskLevel(level_str)
                self.risk_thresholds[level] = required
            except ValueError:
                continue

        self.context = state.get("context", {})

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_current_timestamp() -> float:
        """获取当前时间戳（毫秒）"""
        import time
        return time.time() * 1000