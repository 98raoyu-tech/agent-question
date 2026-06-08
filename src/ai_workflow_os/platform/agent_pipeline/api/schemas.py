"""
Agent Pipeline 请求/响应Schema

定义流水线管理相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO
from ..domain.enums import PipelineStage, PipelineStatus, PipelineStepStatus

# =============================================================================
# 请求Schema
# =============================================================================


class StartPipelineRequest(BaseModel):
    """启动发布流水线请求"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    operator: str | None = Field(default=None, description="操作者标识")


class ExecuteStageRequest(BaseModel):
    """执行阶段请求"""

    gate_passed: bool = Field(default=True, description="是否通过质量门禁")
    result_data: dict[str, Any] = Field(default_factory=dict, description="阶段执行结果数据")
    operator: str | None = Field(default=None, description="操作者标识")


class ApproveReleaseRequest(BaseModel):
    """批准发布请求"""

    reviewer: str = Field(description="审批者标识")
    notes: str = Field(default="", description="审批意见")
    operator: str | None = Field(default=None, description="操作者标识")


class RejectReleaseRequest(BaseModel):
    """拒绝发布请求"""

    reviewer: str = Field(description="审批者标识")
    reason: str = Field(description="拒绝原因")
    operator: str | None = Field(default=None, description="操作者标识")


class DeployReleaseRequest(BaseModel):
    """部署发布请求"""

    environment: str = Field(default="dev", description="部署环境")
    operator: str | None = Field(default=None, description="操作者标识")


class RollbackReleaseRequest(BaseModel):
    """回滚发布请求"""

    reason: str = Field(default="", description="回滚原因")
    operator: str | None = Field(default=None, description="操作者标识")


# =============================================================================
# 响应Schema
# =============================================================================


class PipelineStepResponse(BaseDTO):
    """流水线步骤响应"""

    pipeline_id: str = Field(description="流水线标识")
    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    stage: PipelineStage = Field(description="流水线阶段")
    status: PipelineStepStatus = Field(description="步骤状态")
    started_at: datetime | None = Field(default=None, description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    error_message: str | None = Field(default=None, description="错误信息")
    result_data: dict[str, Any] = Field(description="步骤结果数据")
    gate_passed: bool = Field(description="是否通过质量门禁")
    trace_id: str | None = Field(default=None, description="链路追踪标识")
    duration_ms: float | None = Field(default=None, description="执行时长（毫秒）")


class PipelineResponse(BaseDTO):
    """流水线响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    status: PipelineStatus = Field(description="流水线状态")
    current_stage: PipelineStage | None = Field(default=None, description="当前执行阶段")
    steps: list[PipelineStepResponse] = Field(description="流水线步骤列表")
    triggered_by: str | None = Field(default=None, description="触发者标识")
    progress_percentage: float = Field(description="进度百分比")
    total_duration_ms: float | None = Field(default=None, description="总执行时长（毫秒）")


class PipelineListResponse(BaseModel):
    """流水线列表响应"""

    items: list[PipelineResponse] = Field(description="流水线列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
