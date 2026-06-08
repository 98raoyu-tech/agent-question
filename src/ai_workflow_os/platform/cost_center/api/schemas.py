"""
成本中心请求/响应Schema

定义成本相关的API请求和响应数据模型。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import BudgetStatus, CostType


# =============================================================================
# 成本记录Schema
# =============================================================================


class CreateUsageRequest(CreateDTO):
    """创建成本使用记录请求"""

    agent_id: str = Field(description="Agent标识")
    cost_type: CostType = Field(description="成本类型")
    amount: float = Field(ge=0, description="成本金额")
    currency: str = Field(default="USD", description="货币单位")
    quantity: float = Field(default=0, ge=0, description="使用数量")
    unit: str = Field(default="", description="计量单位")
    description: str = Field(default="", description="描述")


class UsageResponse(BaseDTO):
    """成本使用记录响应"""

    agent_id: str = Field(description="Agent标识")
    cost_type: CostType = Field(description="成本类型")
    amount: float = Field(description="成本金额")
    currency: str = Field(description="货币单位")
    quantity: float = Field(description="使用数量")
    unit: str = Field(description="计量单位")
    description: str = Field(description="描述")


class UsageListResponse(BaseModel):
    """成本使用记录列表响应"""

    items: list[UsageResponse] = Field(description="记录列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 预算Schema
# =============================================================================


class CreateBudgetRequest(CreateDTO):
    """创建预算请求"""

    name: str = Field(min_length=1, max_length=200, description="预算名称")
    agent_id: str = Field(default="", description="Agent标识（为空表示租户级预算）")
    budget_amount: float = Field(gt=0, description="预算金额")
    currency: str = Field(default="USD", description="货币单位")
    period: str = Field(default="monthly", description="预算周期")
    alert_threshold: float = Field(default=80.0, ge=0, le=100, description="告警阈值百分比")


class BudgetResponse(BaseDTO):
    """预算响应"""

    name: str = Field(description="预算名称")
    agent_id: str = Field(description="Agent标识")
    budget_amount: float = Field(description="预算金额")
    used_amount: float = Field(description="已使用金额")
    remaining_amount: float = Field(description="剩余金额")
    usage_percentage: float = Field(description="使用百分比")
    currency: str = Field(description="货币单位")
    status: BudgetStatus = Field(description="预算状态")
    period: str = Field(description="预算周期")
    alert_threshold: float = Field(description="告警阈值百分比")


class BudgetListResponse(BaseModel):
    """预算列表响应"""

    items: list[BudgetResponse] = Field(description="预算列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
