"""
Agent Lifecycle请求/响应Schema

定义Agent生命周期管理相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import (
    AgentLifecycleState,
    ApprovalStatus,
    DeploymentEnvironment,
    DeploymentStatus,
    DeploymentStrategy,
    EvaluationStatus,
    RollbackStatus,
    TestRunStatus,
    TestType,
)


# =============================================================================
# 请求Schema
# =============================================================================


class CreateAgentLifecycleRequest(CreateDTO):
    """创建Agent生命周期定义请求"""

    name: str = Field(min_length=1, max_length=200, description="Agent名称")
    description: str = Field(default="", max_length=2000, description="Agent描述")
    owner_id: Optional[str] = Field(default=None, description="所有者标识")
    team_id: Optional[str] = Field(default=None, description="所属团队标识")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class UpdateAgentLifecycleRequest(UpdateDTO):
    """更新Agent生命周期定义请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Agent名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="Agent描述")
    owner_id: Optional[str] = Field(default=None, description="所有者标识")
    team_id: Optional[str] = Field(default=None, description="所属团队标识")
    tags: Optional[list[str]] = Field(default=None, description="标签列表")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="扩展元数据")


class TransitionStateRequest(BaseModel):
    """状态转换请求"""

    target_state: AgentLifecycleState = Field(description="目标生命周期状态")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class CreateVersionRequest(BaseModel):
    """创建版本请求"""

    change_log: str = Field(default="", description="变更日志")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class SubmitTestingRequest(BaseModel):
    """提交测试请求"""

    test_name: str = Field(default="", description="测试名称")
    test_type: TestType = Field(default=TestType.UNIT, description="测试类型")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class SubmitEvaluationRequest(BaseModel):
    """提交评估请求"""

    evaluation_name: str = Field(default="", description="评估名称")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class SubmitApprovalRequest(BaseModel):
    """提交审批请求"""

    requested_by: str = Field(description="请求者标识")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class ApproveVersionRequest(BaseModel):
    """批准版本请求"""

    reviewer: str = Field(description="审批者标识")
    notes: str = Field(default="", description="审批意见")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class RejectVersionRequest(BaseModel):
    """拒绝版本请求"""

    reviewer: str = Field(description="审批者标识")
    reason: str = Field(description="拒绝原因")
    operator: Optional[str] = Field(default=None, description="操作者标识")


class DeployVersionRequest(BaseModel):
    """部署版本请求"""

    environment: DeploymentEnvironment = Field(
        default=DeploymentEnvironment.DEV,
        description="部署环境",
    )
    deployment_strategy: DeploymentStrategy = Field(
        default=DeploymentStrategy.DIRECT,
        description="部署策略",
    )
    operator: Optional[str] = Field(default=None, description="操作者标识")


class RollbackDeploymentRequest(BaseModel):
    """回滚部署请求"""

    reason: str = Field(default="", description="回滚原因")
    to_version_id: str = Field(default="", description="回滚目标版本标识")
    operator: Optional[str] = Field(default=None, description="操作者标识")


# =============================================================================
# 响应Schema
# =============================================================================


class AgentLifecycleResponse(BaseDTO):
    """Agent生命周期定义响应"""

    name: str = Field(description="Agent名称")
    description: str = Field(description="Agent描述")
    lifecycle_state: AgentLifecycleState = Field(description="当前生命周期状态")
    current_version_id: Optional[str] = Field(default=None, description="当前版本标识")
    owner_id: Optional[str] = Field(default=None, description="所有者标识")
    team_id: Optional[str] = Field(default=None, description="所属团队标识")
    tags: list[str] = Field(description="标签列表")


class AgentLifecycleListResponse(BaseModel):
    """Agent生命周期定义列表响应"""

    items: list[AgentLifecycleResponse] = Field(description="Agent列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class AgentVersionResponse(BaseDTO):
    """Agent版本响应"""

    agent_id: str = Field(description="Agent标识")
    version_number: str = Field(description="版本号")
    change_log: str = Field(description="变更日志")
    is_current: bool = Field(description="是否为当前版本")
    lifecycle_state: AgentLifecycleState = Field(description="版本生命周期状态")
    approval_status: ApprovalStatus = Field(description="审批状态")
    approved_by: Optional[str] = Field(default=None, description="审批者标识")
    approved_at: Optional[datetime] = Field(default=None, description="审批时间")
    rejection_reason: Optional[str] = Field(default=None, description="拒绝原因")


class TestRunResponse(BaseDTO):
    """测试运行响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    test_name: str = Field(description="测试名称")
    status: TestRunStatus = Field(description="测试状态")
    test_type: TestType = Field(description="测试类型")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    pass_rate: float = Field(description="通过率")


class EvaluationResponse(BaseDTO):
    """评估响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    evaluation_name: str = Field(description="评估名称")
    status: EvaluationStatus = Field(description="评估状态")
    accuracy: float = Field(description="准确率")
    latency_ms: float = Field(description="平均延迟")
    cost: float = Field(description="单次调用成本")
    success_rate: float = Field(description="成功率")
    hallucination_rate: float = Field(description="幻觉率")
    groundedness_score: float = Field(description="基于事实评分")
    safety_score: float = Field(description="安全评分")
    overall_score: float = Field(description="综合评分")
    passed: bool = Field(description="是否通过质量门禁")


class ApprovalResponse(BaseDTO):
    """审批响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    approval_status: ApprovalStatus = Field(description="审批状态")
    requested_by: Optional[str] = Field(default=None, description="请求者标识")
    reviewed_by: Optional[str] = Field(default=None, description="审批者标识")
    review_notes: Optional[str] = Field(default=None, description="审批意见")
    requested_at: Optional[datetime] = Field(default=None, description="请求时间")
    reviewed_at: Optional[datetime] = Field(default=None, description="审批时间")
    approval_chain: list[dict[str, Any]] = Field(description="审批链记录")


class DeploymentResponse(BaseDTO):
    """部署响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    environment: DeploymentEnvironment = Field(description="部署环境")
    deployment_strategy: DeploymentStrategy = Field(description="部署策略")
    status: DeploymentStatus = Field(description="部署状态")
    deployed_at: Optional[datetime] = Field(default=None, description="部署完成时间")
    rolled_back_at: Optional[datetime] = Field(default=None, description="回滚时间")
    health_check_url: Optional[str] = Field(default=None, description="健康检查地址")
    traffic_percentage: int = Field(description="流量百分比")
    replicas: int = Field(description="副本数")


class RollbackResponse(BaseDTO):
    """回滚响应"""

    agent_id: str = Field(description="Agent标识")
    from_version_id: str = Field(description="回滚源版本标识")
    to_version_id: str = Field(description="回滚目标版本标识")
    reason: str = Field(description="回滚原因")
    status: RollbackStatus = Field(description="回滚状态")
    initiated_by: Optional[str] = Field(default=None, description="发起者标识")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")
