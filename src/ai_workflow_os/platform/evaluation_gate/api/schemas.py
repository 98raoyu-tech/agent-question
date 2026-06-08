"""
评估门控请求/响应Schema

定义质量门控和评估报告相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import EvaluationTargetType, GateStatus


# =============================================================================
# 质量门控Schema
# =============================================================================


class CreateGateRequest(CreateDTO):
    """创建质量门控请求"""

    name: str = Field(min_length=1, max_length=200, description="门控名称")
    description: str = Field(default="", max_length=2000, description="门控描述")
    target_type: EvaluationTargetType = Field(description="评估目标类型")
    metrics_thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="指标阈值映射（MetricType值 -> 阈值）",
    )
    is_blocking: bool = Field(default=True, description="是否为阻断门控")
    priority: int = Field(default=0, ge=0, description="优先级")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class GateResponse(BaseDTO):
    """质量门控响应"""

    name: str = Field(description="门控名称")
    description: str = Field(description="门控描述")
    target_type: EvaluationTargetType = Field(description="评估目标类型")
    gate_status: GateStatus = Field(description="门控状态")
    metrics_thresholds: dict[str, float] = Field(description="指标阈值映射")
    is_blocking: bool = Field(description="是否为阻断门控")
    priority: int = Field(description="优先级")
    metadata: dict[str, Any] = Field(description="扩展元数据")


class GateListResponse(BaseModel):
    """门控列表响应"""

    items: list[GateResponse] = Field(description="门控列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 评估Schema
# =============================================================================


class EvaluateTargetRequest(CreateDTO):
    """评估目标请求"""

    target_id: str = Field(description="评估目标标识")
    target_type: EvaluationTargetType = Field(description="评估目标类型")
    metric_scores: dict[str, float] = Field(
        min_length=1,
        description="指标评分映射（MetricType值 -> 评分）",
    )


class ReportResponse(BaseDTO):
    """评估报告响应"""

    target_id: str = Field(description="评估目标标识")
    target_type: EvaluationTargetType = Field(description="评估目标类型")
    gate_id: str = Field(description="关联的门控标识")
    gate_name: str = Field(description="关联的门控名称")
    status: GateStatus = Field(description="评估状态")
    metric_scores: dict[str, float] = Field(description="指标评分映射")
    overall_score: float = Field(description="综合评分")
    passed: bool = Field(description="是否通过")
    evaluated_at: Optional[datetime] = Field(default=None, description="评估时间")
    evaluator: str = Field(description="评估执行者")
    details: dict[str, Any] = Field(description="评估详情")
    recommendations: list[str] = Field(description="改进建议列表")


class ReportListResponse(BaseModel):
    """报告列表响应"""

    items: list[ReportResponse] = Field(description="报告列表")
    total: int = Field(description="总数")


# =============================================================================
# 豁免Schema
# =============================================================================


class WaiveGateRequest(BaseModel):
    """豁免门控请求"""

    operator: str = Field(min_length=1, description="操作者标识")
    reason: str = Field(min_length=1, max_length=2000, description="豁免原因")


# =============================================================================
# 发布检查Schema
# =============================================================================


class PublishableResponse(BaseModel):
    """发布检查响应"""

    target_id: str = Field(description="评估目标标识")
    target_type: EvaluationTargetType = Field(description="评估目标类型")
    publishable: bool = Field(description="是否可以发布")
