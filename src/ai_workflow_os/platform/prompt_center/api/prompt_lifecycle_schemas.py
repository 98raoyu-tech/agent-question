"""
Prompt生命周期请求/响应Schema

定义Prompt实验、基准测试、审批、发布和回滚相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.prompt_approval import ApprovalStatus
from ..domain.prompt_benchmark import BenchmarkStatus
from ..domain.prompt_experiment import ExperimentStatus
from ..domain.prompt_release import ReleaseStatus
from ..domain.prompt_rollback import RollbackStatus

# =============================================================================
# 请求Schema
# =============================================================================


class CreateExperimentRequest(CreateDTO):
    """创建实验请求"""

    prompt_id: str = Field(description="Prompt模板标识")
    experiment_name: str = Field(default="", max_length=200, description="实验名称")
    variant_a_version_id: str = Field(description="变体A版本标识")
    variant_b_version_id: str = Field(description="变体B版本标识")
    traffic_split: float = Field(default=0.5, ge=0, le=1, description="变体A流量比例")
    sample_size: int = Field(default=1000, ge=1, description="样本大小")


class StartExperimentRequest(BaseModel):
    """启动实验请求"""

    operator: str | None = Field(default=None, description="操作者标识")


class CompleteExperimentRequest(BaseModel):
    """完成实验请求"""

    winner_version_id: str = Field(description="获胜版本标识")
    operator: str | None = Field(default=None, description="操作者标识")


class RunBenchmarkRequest(CreateDTO):
    """运行基准测试请求"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")
    benchmark_name: str = Field(default="", max_length=200, description="基准测试名称")
    test_cases: list[dict[str, Any]] = Field(min_length=1, description="测试用例列表")


class SubmitApprovalRequest(CreateDTO):
    """提交审批请求"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")


class ApproveVersionRequest(BaseModel):
    """批准版本请求"""

    approver: str = Field(description="审批人标识")
    notes: str | None = Field(default=None, max_length=2000, description="审批备注")
    operator: str | None = Field(default=None, description="操作者标识")


class RejectVersionRequest(BaseModel):
    """拒绝版本请求"""

    approver: str = Field(description="审批人标识")
    reason: str = Field(min_length=1, max_length=2000, description="拒绝原因")
    operator: str | None = Field(default=None, description="操作者标识")


class ReleaseVersionRequest(CreateDTO):
    """发布版本请求"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")
    release_name: str = Field(min_length=1, max_length=200, description="发布名称")
    release_notes: str = Field(default="", max_length=5000, description="发布说明")
    environment: str = Field(min_length=1, max_length=100, description="部署环境")


class RollbackReleaseRequest(BaseModel):
    """回滚发布请求"""

    to_version_id: str = Field(description="目标版本标识")
    reason: str = Field(min_length=1, max_length=2000, description="回滚原因")
    operator: str | None = Field(default=None, description="操作者标识")


# =============================================================================
# 响应Schema
# =============================================================================


class ExperimentResponse(BaseDTO):
    """实验响应"""

    prompt_id: str = Field(description="Prompt模板标识")
    experiment_name: str = Field(description="实验名称")
    variant_a_version_id: str = Field(description="变体A版本标识")
    variant_b_version_id: str = Field(description="变体B版本标识")
    status: ExperimentStatus = Field(description="实验状态")
    traffic_split: float = Field(description="变体A流量比例")
    sample_size: int = Field(description="样本大小")
    started_at: datetime | None = Field(default=None, description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    results: dict[str, Any] = Field(default_factory=dict, description="实验结果")
    winner_version_id: str | None = Field(default=None, description="获胜版本标识")


class BenchmarkResponse(BaseDTO):
    """基准测试响应"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")
    benchmark_name: str = Field(description="基准测试名称")
    test_cases: list[dict[str, Any]] = Field(description="测试用例列表")
    status: BenchmarkStatus = Field(description="测试状态")
    avg_score: float = Field(description="平均评分")
    avg_latency_ms: float = Field(description="平均延迟（毫秒）")
    avg_cost: float = Field(description="平均成本")
    total_tokens: int = Field(description="总Token数")
    results: list[dict[str, Any]] = Field(description="测试结果")
    completed_at: datetime | None = Field(default=None, description="完成时间")


class ApprovalResponse(BaseDTO):
    """审批响应"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")
    requested_by: str = Field(description="申请人标识")
    approved_by: str | None = Field(default=None, description="审批人标识")
    status: ApprovalStatus = Field(description="审批状态")
    requested_at: datetime | None = Field(default=None, description="申请时间")
    approved_at: datetime | None = Field(default=None, description="审批时间")
    approval_notes: str | None = Field(default=None, description="审批备注")
    rejection_reason: str | None = Field(default=None, description="拒绝原因")
    criteria: dict[str, Any] = Field(default_factory=dict, description="审批标准")


class ReleaseResponse(BaseDTO):
    """发布响应"""

    prompt_id: str = Field(description="Prompt模板标识")
    version_id: str = Field(description="版本标识")
    release_name: str = Field(description="发布名称")
    release_notes: str = Field(description="发布说明")
    status: ReleaseStatus = Field(description="发布状态")
    deployed_at: datetime | None = Field(default=None, description="部署时间")
    rolled_back_at: datetime | None = Field(default=None, description="回滚时间")
    traffic_percentage: int = Field(description="流量百分比")
    environment: str = Field(description="部署环境")


class RollbackResponse(BaseDTO):
    """回滚响应"""

    prompt_id: str = Field(description="Prompt模板标识")
    from_version_id: str = Field(description="来源版本标识")
    to_version_id: str = Field(description="目标版本标识")
    reason: str = Field(description="回滚原因")
    status: RollbackStatus = Field(description="回滚状态")
    initiated_by: str = Field(description="发起人标识")
    completed_at: datetime | None = Field(default=None, description="完成时间")


class ExperimentListResponse(BaseModel):
    """实验列表响应"""

    items: list[ExperimentResponse] = Field(description="实验列表")


class BenchmarkListResponse(BaseModel):
    """基准测试列表响应"""

    items: list[BenchmarkResponse] = Field(description="基准测试列表")


class ApprovalListResponse(BaseModel):
    """审批列表响应"""

    items: list[ApprovalResponse] = Field(description="审批列表")


class ReleaseListResponse(BaseModel):
    """发布列表响应"""

    items: list[ReleaseResponse] = Field(description="发布列表")
