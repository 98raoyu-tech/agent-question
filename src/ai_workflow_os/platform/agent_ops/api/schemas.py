"""
Agent Ops 请求/响应Schema

定义Agent运维管理相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import (
    DeploymentStatus,
    DeploymentStrategy,
    Environment,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
)


# =============================================================================
# 部署相关Schema
# =============================================================================


class CreateDeploymentRequest(CreateDTO):
    """创建部署请求"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    environment: Environment = Field(default=Environment.DEV, description="部署环境")
    strategy: DeploymentStrategy = Field(
        default=DeploymentStrategy.DIRECT,
        description="部署策略",
    )
    config: dict[str, Any] = Field(default_factory=dict, description="部署配置")


class UpdateDeploymentRequest(UpdateDTO):
    """更新部署请求"""

    config: Optional[dict[str, Any]] = Field(default=None, description="部署配置")


class PromoteCanaryRequest(BaseModel):
    """提升灰度比例请求"""

    percentage: int = Field(ge=0, le=100, description="目标灰度百分比（0-100）")


class DeploymentResponse(BaseDTO):
    """部署响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    environment: Environment = Field(description="部署环境")
    strategy: DeploymentStrategy = Field(description="部署策略")
    status: DeploymentStatus = Field(description="部署状态")
    canary_percentage: int = Field(description="灰度发布百分比")
    blue_green_active_slot: str = Field(description="蓝绿部署活跃槽位")
    deployed_at: Optional[datetime] = Field(default=None, description="部署完成时间")
    config: dict[str, Any] = Field(description="部署配置")
    health_status: HealthStatus = Field(description="健康状态")


class DeploymentListResponse(BaseModel):
    """部署列表响应"""

    items: list[DeploymentResponse] = Field(description="部署列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 事故相关Schema
# =============================================================================


class TimelineEntrySchema(BaseModel):
    """时间线条目Schema"""

    timestamp: datetime = Field(description="时间戳")
    action: str = Field(description="操作描述")
    operator: Optional[str] = Field(default=None, description="操作者")
    details: dict[str, Any] = Field(default_factory=dict, description="详细信息")


class CreateIncidentRequest(CreateDTO):
    """创建事故请求"""

    agent_id: str = Field(default="", description="Agent标识")
    title: str = Field(min_length=1, max_length=200, description="事故标题")
    description: str = Field(default="", max_length=5000, description="事故描述")
    severity: IncidentSeverity = Field(default=IncidentSeverity.LOW, description="严重程度")
    environment: Environment = Field(default=Environment.DEV, description="发生环境")


class UpdateIncidentStatusRequest(BaseModel):
    """更新事故状态请求"""

    status: IncidentStatus = Field(description="目标状态")
    root_cause: Optional[str] = Field(default=None, description="根本原因（解决时需要）")
    resolution: Optional[str] = Field(default=None, description="解决方案（解决时需要）")


class IncidentResponse(BaseDTO):
    """事故响应"""

    agent_id: str = Field(description="Agent标识")
    title: str = Field(description="事故标题")
    description: str = Field(description="事故描述")
    severity: IncidentSeverity = Field(description="严重程度")
    status: IncidentStatus = Field(description="事故状态")
    assigned_to: Optional[str] = Field(default=None, description="分配给")
    environment: Environment = Field(description="发生环境")
    detected_at: datetime = Field(description="检测时间")
    resolved_at: Optional[datetime] = Field(default=None, description="解决时间")
    root_cause: Optional[str] = Field(default=None, description="根本原因")
    resolution: Optional[str] = Field(default=None, description="解决方案")
    timeline: list[TimelineEntrySchema] = Field(description="时间线记录")


class IncidentListResponse(BaseModel):
    """事故列表响应"""

    items: list[IncidentResponse] = Field(description="事故列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 运维手册相关Schema
# =============================================================================


class RunbookStepSchema(BaseModel):
    """运维手册步骤Schema"""

    step_id: str = Field(default="", description="步骤标识")
    title: str = Field(description="步骤标题")
    description: str = Field(default="", description="步骤描述")
    action_type: str = Field(default="manual", description="操作类型（manual/automated）")
    command: Optional[str] = Field(default=None, description="执行命令")
    expected_result: Optional[str] = Field(default=None, description="预期结果")


class RunbookExecutionResponse(BaseModel):
    """运维手册执行响应"""

    execution_id: str = Field(description="执行标识")
    executed_at: datetime = Field(description="执行时间")
    executed_by: Optional[str] = Field(default=None, description="执行者")
    context: dict[str, Any] = Field(description="执行上下文")
    status: str = Field(description="执行状态")
    result: Optional[str] = Field(default=None, description="执行结果")


class CreateRunbookRequest(CreateDTO):
    """创建运维手册请求"""

    name: str = Field(min_length=1, max_length=200, description="手册名称")
    description: str = Field(default="", max_length=2000, description="手册描述")
    agent_id: str = Field(default="", description="Agent标识")
    trigger_condition: str = Field(default="", description="触发条件描述")
    steps: list[RunbookStepSchema] = Field(default_factory=list, description="操作步骤列表")


class ExecuteRunbookRequest(BaseModel):
    """执行运维手册请求"""

    context: dict[str, Any] = Field(default_factory=dict, description="执行上下文")


class RunbookResponse(BaseDTO):
    """运维手册响应"""

    name: str = Field(description="手册名称")
    description: str = Field(description="手册描述")
    agent_id: str = Field(description="Agent标识")
    trigger_condition: str = Field(description="触发条件描述")
    steps: list[RunbookStepSchema] = Field(description="操作步骤列表")
    is_active: bool = Field(description="是否激活")
    last_executed_at: Optional[datetime] = Field(default=None, description="最后执行时间")
    execution_count: int = Field(description="执行次数")


class RunbookListResponse(BaseModel):
    """运维手册列表响应"""

    items: list[RunbookResponse] = Field(description="运维手册列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# SLA相关Schema
# =============================================================================


class CreateSLARequest(CreateDTO):
    """创建SLA请求"""

    name: str = Field(min_length=1, max_length=200, description="SLA名称")
    agent_id: str = Field(default="", description="Agent标识")
    target_uptime: float = Field(default=99.9, ge=0, le=100, description="目标正常运行时间百分比")
    target_latency_p99_ms: float = Field(default=500.0, ge=0, description="目标P99延迟（毫秒）")
    target_success_rate: float = Field(default=99.5, ge=0, le=100, description="目标成功率百分比")
    target_availability: float = Field(default=99.99, ge=0, le=100, description="目标可用性百分比")
    period_days: int = Field(default=30, ge=1, description="评估周期（天）")


class UpdateSLAMetricsRequest(BaseModel):
    """更新SLA指标请求"""

    uptime: float = Field(ge=0, le=100, description="正常运行时间百分比")
    latency: float = Field(ge=0, description="P99延迟（毫秒）")
    success_rate: float = Field(ge=0, le=100, description="成功率百分比")
    availability: float = Field(ge=0, le=100, description="可用性百分比")


class SLAComplianceDetailsSchema(BaseModel):
    """SLA合规详情Schema"""

    target: float = Field(description="目标值")
    current: float = Field(description="当前值")
    met: bool = Field(description="是否达标")


class SLAResponse(BaseDTO):
    """SLA响应"""

    name: str = Field(description="SLA名称")
    agent_id: str = Field(description="Agent标识")
    target_uptime: float = Field(description="目标正常运行时间百分比")
    target_latency_p99_ms: float = Field(description="目标P99延迟（毫秒）")
    target_success_rate: float = Field(description="目标成功率百分比")
    target_availability: float = Field(description="目标可用性百分比")
    period_days: int = Field(description="评估周期（天）")
    current_uptime: float = Field(description="当前正常运行时间百分比")
    current_latency_p99: float = Field(description="当前P99延迟（毫秒）")
    current_success_rate: float = Field(description="当前成功率百分比")
    current_availability: float = Field(description="当前可用性百分比")
    is_met: bool = Field(description="是否满足SLA")
    error_budget: float = Field(default=100.0, description="剩余错误预算百分比")
    compliance_details: Optional[dict[str, SLAComplianceDetailsSchema]] = Field(
        default=None,
        description="合规详情",
    )


class SLAListResponse(BaseModel):
    """SLA列表响应"""

    items: list[SLAResponse] = Field(description="SLA列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# SLO相关Schema
# =============================================================================


class CreateSLORequest(CreateDTO):
    """创建SLO请求"""

    name: str = Field(min_length=1, max_length=200, description="SLO名称")
    agent_id: str = Field(default="", description="Agent标识")
    sla_id: str = Field(default="", description="关联的SLA标识")
    metric_name: str = Field(min_length=1, description="指标名称")
    target_value: float = Field(description="目标值")
    period_days: int = Field(default=30, ge=1, description="评估周期（天）")


class UpdateSLOValueRequest(BaseModel):
    """更新SLO当前值请求"""

    value: float = Field(description="当前值")


class SLOResponse(BaseDTO):
    """SLO响应"""

    name: str = Field(description="SLO名称")
    agent_id: str = Field(description="Agent标识")
    sla_id: str = Field(description="关联的SLA标识")
    metric_name: str = Field(description="指标名称")
    target_value: float = Field(description="目标值")
    current_value: float = Field(description="当前值")
    error_budget_remaining: float = Field(description="剩余错误预算百分比")
    burn_rate: float = Field(description="错误预算消耗速率")
    period_days: int = Field(description="评估周期（天）")
    is_burning_too_fast: bool = Field(default=False, description="是否消耗过快")
    remaining_days: Optional[float] = Field(default=None, description="预计剩余天数")


class SLOListResponse(BaseModel):
    """SLO列表响应"""

    items: list[SLOResponse] = Field(description="SLO列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
