"""
Agent Registry请求/响应Schema

定义Agent注册相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import AgentRegistryStatus, FrameworkType, HealthStatus

# =============================================================================
# 请求Schema
# =============================================================================


class RegisterAgentRequest(CreateDTO):
    """注册Agent请求"""

    name: str = Field(min_length=1, max_length=200, description="Agent名称")
    description: str = Field(default="", max_length=2000, description="Agent描述")
    version: str = Field(default="1.0.0", max_length=50, description="Agent版本号")
    framework: FrameworkType = Field(default=FrameworkType.CUSTOM, description="Agent框架类型")
    model_name: str = Field(default="", max_length=200, description="模型名称")
    owner_id: str = Field(default="", description="所有者标识")
    team_id: str = Field(default="", description="所属团队标识")
    endpoint: str | None = Field(default=None, max_length=500, description="Agent服务端点")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    capabilities: list[str] = Field(default_factory=list, description="能力列表")


class UpdateAgentRequest(UpdateDTO):
    """更新Agent请求"""

    name: str | None = Field(default=None, min_length=1, max_length=200, description="Agent名称")
    description: str | None = Field(default=None, max_length=2000, description="Agent描述")
    version: str | None = Field(default=None, max_length=50, description="Agent版本号")
    framework: FrameworkType | None = Field(default=None, description="Agent框架类型")
    model_name: str | None = Field(default=None, max_length=200, description="模型名称")
    owner_id: str | None = Field(default=None, description="所有者标识")
    team_id: str | None = Field(default=None, description="所属团队标识")
    endpoint: str | None = Field(default=None, max_length=500, description="Agent服务端点")
    tags: list[str] | None = Field(default=None, description="标签列表")
    metadata: dict[str, Any] | None = Field(default=None, description="扩展元数据")
    capabilities: list[str] | None = Field(default=None, description="能力列表")


# =============================================================================
# 响应Schema
# =============================================================================


class AgentRegistrationResponse(BaseDTO):
    """Agent注册响应"""

    name: str = Field(description="Agent名称")
    description: str = Field(description="Agent描述")
    version: str = Field(description="Agent版本号")
    framework: FrameworkType = Field(description="Agent框架类型")
    model_name: str = Field(description="模型名称")
    owner_id: str = Field(description="所有者标识")
    team_id: str = Field(description="所属团队标识")
    endpoint: str | None = Field(default=None, description="Agent服务端点")
    status: AgentRegistryStatus = Field(description="Agent注册状态")
    health_status: HealthStatus = Field(description="Agent健康状态")
    tags: list[str] = Field(description="标签列表")
    metadata: dict[str, Any] = Field(description="扩展元数据")
    capabilities: list[str] = Field(description="能力列表")


class AgentRuntimeInfoResponse(BaseDTO):
    """Agent运行时信息响应"""

    agent_registration_id: str = Field(description="关联的Agent注册标识")
    instance_id: str = Field(description="运行实例标识")
    host: str = Field(description="实例主机地址")
    port: int = Field(description="实例端口号")
    pid: int | None = Field(default=None, description="进程ID")
    uptime_seconds: float = Field(description="运行时长（秒）")
    request_count: int = Field(description="累计请求数")
    error_count: int = Field(description="累计错误数")
    avg_latency_ms: float = Field(description="平均延迟（毫秒）")
    last_heartbeat: datetime | None = Field(default=None, description="最近心跳时间")
    status: HealthStatus = Field(description="健康状态")
    error_rate: float = Field(description="错误率")
    is_responsive: bool = Field(description="是否响应正常")


class AgentRegistrationListResponse(BaseModel):
    """Agent注册列表响应"""

    items: list[AgentRegistrationResponse] = Field(description="Agent注册列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
