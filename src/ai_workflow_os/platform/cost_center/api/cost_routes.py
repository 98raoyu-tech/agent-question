"""
成本中心 FastAPI路由

提供成本记录和预算管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.cost_service import CostService
from ..domain.cost_budget import CostBudget
from ..domain.cost_usage import CostUsage
from ..domain.enums import CostType
from ..infrastructure.cost_repository import CostRepository
from .schemas import (
    BudgetListResponse,
    BudgetResponse,
    CreateBudgetRequest,
    CreateUsageRequest,
    UsageListResponse,
    UsageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cost-center", tags=["成本中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_cost_repository = CostRepository()
_cost_service = CostService(_cost_repository)


@router.post(
    "/usages",
    response_model=UsageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="记录成本使用",
    description="记录一次资源使用成本",
)
async def record_usage(request: CreateUsageRequest) -> UsageResponse:
    """记录成本使用"""
    try:
        usage = CostUsage(
            agent_id=request.agent_id,
            cost_type=request.cost_type,
            amount=request.amount,
            currency=request.currency,
            quantity=request.quantity,
            unit=request.unit,
            description=request.description,
            tenant_id=request.tenant_id,
        )

        created_usage = await _cost_service.record_usage(usage)

        return _to_usage_response(created_usage)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/usages",
    response_model=UsageListResponse,
    summary="查询成本使用记录",
    description="分页查询成本使用记录",
)
async def list_usages(
    agent_id: Optional[str] = Query(default=None, description="Agent标识"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> UsageListResponse:
    """查询成本使用记录"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _cost_service.list_usages(agent_id, pagination)

    return UsageListResponse(
        items=[_to_usage_response(u) for u in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post(
    "/budgets",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建预算",
    description="创建一个新的预算",
)
async def create_budget(request: CreateBudgetRequest) -> BudgetResponse:
    """创建预算"""
    try:
        budget = CostBudget(
            name=request.name,
            agent_id=request.agent_id,
            budget_amount=request.budget_amount,
            currency=request.currency,
            period=request.period,
            alert_threshold=request.alert_threshold,
            tenant_id=request.tenant_id,
        )

        created_budget = await _cost_service.create_budget(budget)

        return _to_budget_response(created_budget)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/budgets/{budget_id}",
    response_model=BudgetResponse,
    summary="获取预算详情",
    description="根据ID获取预算的详细信息",
)
async def get_budget(budget_id: str) -> BudgetResponse:
    """获取预算详情"""
    try:
        budget = await _cost_service.get_budget(budget_id)
        return _to_budget_response(budget)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/budgets",
    response_model=BudgetListResponse,
    summary="查询预算列表",
    description="分页查询预算列表",
)
async def list_budgets(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> BudgetListResponse:
    """查询预算列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _cost_service.list_budgets(pagination, tenant_id)

    return BudgetListResponse(
        items=[_to_budget_response(b) for b in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


def _to_usage_response(usage: CostUsage) -> UsageResponse:
    """将成本使用记录转换为响应Schema"""
    return UsageResponse(
        id=usage.id,
        agent_id=usage.agent_id,
        cost_type=usage.cost_type,
        amount=usage.amount,
        currency=usage.currency,
        quantity=usage.quantity,
        unit=usage.unit,
        description=usage.description,
        created_at=usage.created_at,
        updated_at=usage.updated_at,
        tenant_id=usage.tenant_id,
    )


def _to_budget_response(budget: CostBudget) -> BudgetResponse:
    """将预算实体转换为响应Schema"""
    return BudgetResponse(
        id=budget.id,
        name=budget.name,
        agent_id=budget.agent_id,
        budget_amount=budget.budget_amount,
        used_amount=budget.used_amount,
        remaining_amount=budget.remaining_amount,
        usage_percentage=budget.usage_percentage,
        currency=budget.currency,
        status=budget.status,
        period=budget.period,
        alert_threshold=budget.alert_threshold,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        tenant_id=budget.tenant_id,
    )
