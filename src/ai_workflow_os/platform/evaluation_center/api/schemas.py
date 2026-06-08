"""
评估中心请求/响应Schema

定义评测相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import MetricType, RunStatus


# =============================================================================
# 数据集Schema
# =============================================================================


class CreateDatasetRequest(CreateDTO):
    """创建评测数据集请求"""

    name: str = Field(min_length=1, max_length=200, description="数据集名称")
    description: str = Field(default="", max_length=2000, description="数据集描述")
    agent_id: str = Field(description="关联的Agent标识")
    test_cases: list[dict[str, Any]] = Field(default_factory=list, description="测试用例列表")
    metrics: list[str] = Field(default_factory=list, description="评测指标列表")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class DatasetResponse(BaseDTO):
    """评测数据集响应"""

    name: str = Field(description="数据集名称")
    description: str = Field(description="数据集描述")
    agent_id: str = Field(description="关联的Agent标识")
    test_cases: list[dict[str, Any]] = Field(description="测试用例列表")
    metrics: list[str] = Field(description="评测指标列表")
    tags: list[str] = Field(description="标签列表")


class DatasetListResponse(BaseModel):
    """数据集列表响应"""

    items: list[DatasetResponse] = Field(description="数据集列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 运行Schema
# =============================================================================


class CreateRunRequest(CreateDTO):
    """创建评测运行请求"""

    dataset_id: str = Field(description="数据集标识")
    agent_id: str = Field(description="Agent标识")
    run_name: str = Field(default="", description="运行名称")
    config: dict[str, Any] = Field(default_factory=dict, description="运行配置")


class RunResponse(BaseDTO):
    """评测运行响应"""

    dataset_id: str = Field(description="数据集标识")
    agent_id: str = Field(description="Agent标识")
    run_name: str = Field(description="运行名称")
    status: RunStatus = Field(description="运行状态")
    total_cases: int = Field(description="总测试用例数")
    completed_cases: int = Field(description="已完成用例数")
    failed_cases: int = Field(description="失败用例数")
    progress: float = Field(description="运行进度")
    success_rate: float = Field(description="成功率")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class RunListResponse(BaseModel):
    """运行列表响应"""

    items: list[RunResponse] = Field(description="运行列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
