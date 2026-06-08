"""
适配器请求/响应Schema

定义适配器相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO
from ..domain.enums import AdapterStatus, AdapterType, InvocationStatus

# =============================================================================
# 请求Schema
# =============================================================================


class RegisterAdapterRequest(BaseModel):
    """注册适配器请求"""

    adapter_type: AdapterType = Field(description="适配器类型")
    config: dict[str, Any] = Field(default_factory=dict, description="适配器配置")
    operator: str | None = Field(default=None, description="操作者标识")


class InvokeAgentRequest(BaseModel):
    """调用Agent请求"""

    adapter_id: str = Field(description="适配器标识")
    agent_id: str = Field(description="Agent标识")
    input_data: dict[str, Any] = Field(description="输入数据")
    config: dict[str, Any] = Field(default_factory=dict, description="调用级配置")
    operator: str | None = Field(default=None, description="操作者标识")


# =============================================================================
# 响应Schema
# =============================================================================


class AdapterResponse(BaseDTO):
    """适配器响应"""

    adapter_type: AdapterType = Field(description="适配器类型")
    status: AdapterStatus = Field(description="适配器状态")
    config: dict[str, Any] = Field(default_factory=dict, description="适配器配置")


class InvocationResponse(BaseDTO):
    """调用记录响应"""

    adapter_type: AdapterType = Field(description="适配器类型")
    agent_id: str = Field(description="Agent标识")
    input_data: dict[str, Any] = Field(description="输入数据")
    output_data: dict[str, Any] = Field(description="输出数据")
    status: InvocationStatus = Field(description="调用状态")
    started_at: datetime = Field(description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    error_message: str | None = Field(default=None, description="错误信息")
    latency_ms: float | None = Field(default=None, description="延迟（毫秒）")
    token_usage: dict[str, Any] | None = Field(default=None, description="Token使用量")


class InvocationListResponse(BaseModel):
    """调用记录列表响应"""

    items: list[InvocationResponse] = Field(description="调用记录列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class AdapterListResponse(BaseModel):
    """适配器列表响应"""

    items: list[AdapterResponse] = Field(description="适配器列表")
