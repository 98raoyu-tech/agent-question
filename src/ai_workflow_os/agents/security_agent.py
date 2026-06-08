"""
Security Agent - 安全检测智能体

负责执行安全检测，包括 Prompt 注入检测、工具权限验证和操作审计。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base import AgentResult, AgentStatus, AgentTask, AgentType, BaseAgent
from .policy_agent import RiskLevel


# ==================== 数据类定义 ====================

@dataclass
class AuditRecord:
    """审计记录数据结构

    Attributes:
        timestamp: 审计时间戳
        agent_id: 操作的 Agent ID
        action: 执行的操作
        resource: 操作的资源
        result: 操作结果
        risk_level: 风险等级
    """
    timestamp: str = ""
    agent_id: str = ""
    action: str = ""
    resource: str = ""
    result: str = ""
    risk_level: RiskLevel = RiskLevel.LOW


# ==================== Security Agent ====================

class SecurityAgent(BaseAgent):
    """安全检测智能体

    负责执行安全检测，保障系统安全。

    Attributes:
        policy_engine: 策略引擎实例
        prompt_firewall: Prompt 防火墙实例
    """

    def __init__(
        self,
        agent_id: str = "",
        agent_name: str = "SecurityAgent",
        policy_engine: Any = None,
        prompt_firewall: Any = None,
    ) -> None:
        """初始化 Security Agent

        Args:
            agent_id: Agent 唯一标识
            agent_name: Agent 名称
            policy_engine: 策略引擎实例
            prompt_firewall: Prompt 防火墙实例
        """
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=AgentType.SECURITY,
        )
        self.policy_engine = policy_engine
        self.prompt_firewall = prompt_firewall

    # ==================== 核心方法 ====================

    async def execute(self, task: AgentTask) -> AgentResult:
        """执行安全检测

        Args:
            task: 包含安全检测请求的任务

        Returns:
            安全检测结果
        """
        self.status = AgentStatus.RUNNING
        start_time = self._get_current_timestamp()

        try:
            # 提取检测参数
            operation = task.payload.get("operation", "scan_prompt")
            prompt = task.payload.get("prompt", "")
            agent_id = task.payload.get("agent_id", "")
            tool_name = task.payload.get("tool_name", "")
            action = task.payload.get("action", {})

            # 根据操作类型执行相应检测
            if operation == "scan_prompt":
                # Prompt 注入检测
                is_injection = await self._scan_prompt_injection(prompt)

                output = {
                    "operation": "scan_prompt",
                    "is_injection": is_injection,
                    "prompt_length": len(prompt),
                    "safe": not is_injection,
                }

            elif operation == "validate_permissions":
                # 工具权限验证
                has_permission = await self._validate_tool_permissions(agent_id, tool_name)

                output = {
                    "operation": "validate_permissions",
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "has_permission": has_permission,
                }

            elif operation == "audit":
                # 审计操作记录
                audit_record = await self._audit_action(action)

                output = {
                    "operation": "audit",
                    "audit_record": {
                        "timestamp": audit_record.timestamp,
                        "agent_id": audit_record.agent_id,
                        "action": audit_record.action,
                        "resource": audit_record.resource,
                        "result": audit_record.result,
                        "risk_level": audit_record.risk_level.value,
                    },
                }

            elif operation == "sandbox":
                # 沙箱执行
                tool_execution = task.payload.get("tool_execution", {})
                sandbox_result = await self._enforce_sandbox(tool_execution)

                output = {
                    "operation": "sandbox",
                    "sandbox_result": sandbox_result,
                }

            else:
                raise ValueError(f"不支持的安全检测操作: {operation}")

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

    async def _scan_prompt_injection(self, prompt: str) -> bool:
        """检测 Prompt 注入

        检查输入的 Prompt 是否包含注入攻击。

        Args:
            prompt: 待检测的 Prompt

        Returns:
            是否检测到注入攻击
        """
        # TODO: 集成实际的 Prompt 防火墙
        if self.prompt_firewall:
            return await self.prompt_firewall.scan(prompt)

        # 基础的注入检测逻辑
        injection_patterns = [
            "ignore previous instructions",
            "忽略之前的指令",
            "system prompt",
            "系统提示",
            "jailbreak",
            "越狱",
            "DAN",
            "developer mode",
            "开发者模式",
        ]

        prompt_lower = prompt.lower()
        for pattern in injection_patterns:
            if pattern.lower() in prompt_lower:
                print(f"[Security] 检测到潜在注入: {pattern}")
                return True

        return False

    async def _validate_tool_permissions(self, agent_id: str, tool_name: str) -> bool:
        """验证工具权限

        检查指定 Agent 是否有权限使用指定工具。

        Args:
            agent_id: Agent ID
            tool_name: 工具名称

        Returns:
            是否有权限
        """
        # TODO: 集成实际的权限管理
        if self.policy_engine:
            return await self.policy_engine.check_tool_permission(agent_id, tool_name)

        # 基础的权限检查逻辑
        restricted_tools = {
            "file_system",
            "database_admin",
            "network_access",
            "system_command",
        }

        if tool_name in restricted_tools:
            print(f"[Security] 受限工具: {tool_name}，需要额外授权")
            return False

        return True

    async def _audit_action(self, action: dict[str, Any]) -> AuditRecord:
        """审计操作记录

        记录操作审计信息。

        Args:
            action: 操作信息

        Returns:
            审计记录
        """
        now = datetime.now(timezone.utc).isoformat()

        # 评估操作风险等级
        risk_level = RiskLevel.LOW
        action_type = action.get("type", "")

        if action_type in ["delete", "deploy", "admin"]:
            risk_level = RiskLevel.HIGH
        elif action_type in ["write", "update"]:
            risk_level = RiskLevel.MEDIUM

        record = AuditRecord(
            timestamp=now,
            agent_id=action.get("agent_id", ""),
            action=action_type,
            resource=action.get("resource", ""),
            result=action.get("result", "pending"),
            risk_level=risk_level,
        )

        # 记录审计日志
        print(f"[Security] 审计记录: {record}")

        return record

    async def _enforce_sandbox(self, tool_execution: dict[str, Any]) -> dict[str, Any]:
        """沙箱执行

        在沙箱环境中执行工具，限制资源访问。

        Args:
            tool_execution: 工具执行信息

        Returns:
            沙箱执行结果
        """
        tool_name = tool_execution.get("tool_name", "unknown")
        params = tool_execution.get("params", {})

        # 沙箱限制配置
        sandbox_config = {
            "max_memory_mb": 512,
            "max_cpu_percent": 50,
            "max_execution_time_seconds": 30,
            "allowed_network": False,
            "allowed_file_system": False,
        }

        # TODO: 集成实际的沙箱执行环境
        print(f"[Security] 沙箱执行: {tool_name}")
        print(f"[Security] 沙箱配置: {sandbox_config}")

        return {
            "tool_name": tool_name,
            "sandbox_config": sandbox_config,
            "status": "completed",
            "output": f"沙箱执行 {tool_name} 完成",
        }

    # ==================== 生命周期方法 ====================

    async def pause(self) -> None:
        """暂停 Security Agent"""
        self.status = AgentStatus.PAUSED

    async def resume(self) -> None:
        """恢复 Security Agent"""
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