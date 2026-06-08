"""
治理中心请求/响应Schema

定义治理相关的API请求和响应数据模型。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import AuditAction, PolicyStatus, PolicyType


# =============================================================================
# 策略Schema
# =============================================================================


class CreatePolicyRequest(CreateDTO):
    """创建策略请求"""

    name: str = Field(min_length=1, max_length=200, description="策略名称")
    description: str = Field(default="", max_length=2000, description="策略描述")
    policy_type: PolicyType = Field(description="策略类型")
    rules: list[dict[str, Any]] = Field(default_factory=list, description="策略规则列表")
    priority: int = Field(default=100, ge=0, description="优先级")
    target_agents: list[str] = Field(default_factory=list, description="适用的Agent列表")


class PolicyResponse(BaseDTO):
    """策略响应"""

    name: str = Field(description="策略名称")
    description: str = Field(description="策略描述")
    policy_type: PolicyType = Field(description="策略类型")
    status: PolicyStatus = Field(description="策略状态")
    rules: list[dict[str, Any]] = Field(description="策略规则列表")
    priority: int = Field(description="优先级")
    target_agents: list[str] = Field(description="适用的Agent列表")


class PolicyListResponse(BaseModel):
    """策略列表响应"""

    items: list[PolicyResponse] = Field(description="策略列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 审计日志Schema
# =============================================================================


class CreateAuditLogRequest(CreateDTO):
    """创建审计日志请求"""

    user_id: str = Field(description="操作用户标识")
    action: AuditAction = Field(description="审计动作")
    resource_type: str = Field(description="资源类型")
    resource_id: str = Field(description="资源标识")
    details: dict[str, Any] = Field(default_factory=dict, description="操作详情")
    ip_address: str = Field(default="", description="IP地址")
    user_agent: str = Field(default="", description="用户代理")
    success: bool = Field(default=True, description="操作是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class AuditLogResponse(BaseDTO):
    """审计日志响应"""

    user_id: str = Field(description="操作用户标识")
    action: AuditAction = Field(description="审计动作")
    resource_type: str = Field(description="资源类型")
    resource_id: str = Field(description="资源标识")
    details: dict[str, Any] = Field(description="操作详情")
    ip_address: str = Field(description="IP地址")
    success: bool = Field(description="操作是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""

    items: list[AuditLogResponse] = Field(description="审计日志列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
