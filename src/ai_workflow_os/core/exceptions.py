"""
异常定义模块

定义统一的异常体系，覆盖 Agent、工作流、工具、记忆、策略等核心领域的异常类型。
所有自定义异常均继承自 WorkflowOSException 基类。
"""


class WorkflowOSException(Exception):
    """
    WorkflowOS 平台基础异常类

    所有业务异常的基类，提供统一的异常信息格式。
    """

    def __init__(self, message: str = "", code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# =============================================================================
# Agent 相关异常
# =============================================================================


class AgentException(WorkflowOSException):
    """Agent 相关异常基类"""

    def __init__(self, message: str = "", code: str = "AGENT_ERROR"):
        super().__init__(message, code)


class AgentScheduleException(AgentException):
    """Agent 调度异常"""

    def __init__(self, message: str = "", agent_id: str = ""):
        self.agent_id = agent_id
        detail = f"Agent 调度失败: {message}" if not agent_id else f"Agent [{agent_id}] 调度失败: {message}"
        super().__init__(detail, "AGENT_SCHEDULE_ERROR")


class AgentTimeoutException(AgentException):
    """Agent 执行超时异常"""

    def __init__(self, message: str = "", agent_id: str = "", timeout: float = 0):
        self.agent_id = agent_id
        self.timeout = timeout
        detail = f"Agent [{agent_id}] 执行超时 ({timeout}s): {message}" if agent_id else f"Agent 执行超时: {message}"
        super().__init__(detail, "AGENT_TIMEOUT_ERROR")


# =============================================================================
# 工作流相关异常
# =============================================================================


class WorkflowException(WorkflowOSException):
    """工作流相关异常基类"""

    def __init__(self, message: str = "", code: str = "WORKFLOW_ERROR"):
        super().__init__(message, code)


class WorkflowNotFoundException(WorkflowException):
    """工作流未找到异常"""

    def __init__(self, workflow_id: str = ""):
        self.workflow_id = workflow_id
        detail = f"工作流未找到: {workflow_id}" if workflow_id else "工作流未找到"
        super().__init__(detail, "WORKFLOW_NOT_FOUND")


class WorkflowExecutionException(WorkflowException):
    """工作流执行异常"""

    def __init__(self, message: str = "", workflow_id: str = "", step: str = ""):
        self.workflow_id = workflow_id
        self.step = step
        parts = ["工作流执行失败"]
        if workflow_id:
            parts.append(f"工作流 [{workflow_id}]")
        if step:
            parts.append(f"步骤 [{step}]")
        detail = f"{' - '.join(parts)}: {message}"
        super().__init__(detail, "WORKFLOW_EXECUTION_ERROR")


# =============================================================================
# 工具相关异常
# =============================================================================


class ToolException(WorkflowOSException):
    """工具相关异常基类"""

    def __init__(self, message: str = "", code: str = "TOOL_ERROR"):
        super().__init__(message, code)


class ToolNotFoundException(ToolException):
    """工具未找到异常"""

    def __init__(self, tool_name: str = ""):
        self.tool_name = tool_name
        detail = f"工具未找到: {tool_name}" if tool_name else "工具未找到"
        super().__init__(detail, "TOOL_NOT_FOUND")


class ToolPermissionDeniedException(ToolException):
    """工具权限拒绝异常"""

    def __init__(self, tool_name: str = "", agent_id: str = ""):
        self.tool_name = tool_name
        self.agent_id = agent_id
        if tool_name and agent_id:
            detail = f"权限拒绝: Agent [{agent_id}] 无权使用工具 [{tool_name}]"
        elif tool_name:
            detail = f"权限拒绝: 无权使用工具 [{tool_name}]"
        else:
            detail = "权限拒绝: 工具访问被拒绝"
        super().__init__(detail, "TOOL_PERMISSION_DENIED")


# =============================================================================
# 记忆相关异常
# =============================================================================


class MemoryException(WorkflowOSException):
    """记忆系统相关异常"""

    def __init__(self, message: str = "", code: str = "MEMORY_ERROR"):
        super().__init__(message, code)


# =============================================================================
# 策略与安全相关异常
# =============================================================================


class PolicyViolationException(WorkflowOSException):
    """策略违规异常"""

    def __init__(self, message: str = "", policy: str = ""):
        self.policy = policy
        detail = f"策略违规 [{policy}]: {message}" if policy else f"策略违规: {message}"
        super().__init__(detail, "POLICY_VIOLATION")


# =============================================================================
# 熔断器相关异常
# =============================================================================


class CircuitBreakerOpenException(WorkflowOSException):
    """熔断器打开异常"""

    def __init__(self, service: str = "", retry_after: float = 0):
        self.service = service
        self.retry_after = retry_after
        detail = f"熔断器已打开: 服务 [{service}] 暂时不可用，请在 {retry_after}s 后重试" if service else "熔断器已打开: 服务暂时不可用"
        super().__init__(detail, "CIRCUIT_BREAKER_OPEN")


# =============================================================================
# 人类审核相关异常
# =============================================================================


class HumanApprovalTimeoutException(WorkflowOSException):
    """人类审核超时异常"""

    def __init__(self, approval_id: str = "", timeout: float = 0):
        self.approval_id = approval_id
        self.timeout = timeout
        detail = f"人类审核超时: 审批 [{approval_id}] 在 {timeout}s 内未完成" if approval_id else "人类审核超时: 审批请求超时未处理"
        super().__init__(detail, "HUMAN_APPROVAL_TIMEOUT")