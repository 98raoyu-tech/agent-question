"""
适配器FastAPI路由

提供Agent适配器管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.adapter_service import AdapterService
from ..domain.adapter_invocation import AdapterInvocation
from ..domain.agent_adapter import AgentAdapter
from ..infrastructure.adapter_repository import AdapterRepository
from .schemas import (
    AdapterListResponse,
    AdapterResponse,
    InvocationListResponse,
    InvocationResponse,
    InvokeAgentRequest,
    RegisterAdapterRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/adapters", tags=["Agent Adapters"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_adapter_repository = AdapterRepository()
_adapter_service = AdapterService(_adapter_repository)


# =============================================================================
# 适配器管理端点
# =============================================================================


@router.post(
    "/adapters",
    response_model=AdapterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册适配器",
    description="注册一个新的Agent适配器",
)
async def register_adapter(request: RegisterAdapterRequest) -> AdapterResponse:
    """注册适配器

    Args:
        request: 注册适配器请求

    Returns:
        注册的适配器响应

    Raises:
        HTTPException: 注册失败
    """
    try:
        adapter = await _adapter_service.register_adapter(
            adapter_type=request.adapter_type,
            config=request.config,
            operator=request.operator,
        )

        return _to_adapter_response(adapter)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/adapters",
    response_model=AdapterListResponse,
    summary="查询适配器列表",
    description="查询所有已注册的适配器",
)
async def list_adapters(
    adapter_type: str | None = Query(default=None, description="适配器类型过滤"),
    adapter_status: str | None = Query(default=None, alias="status", description="状态过滤"),
) -> AdapterListResponse:
    """查询适配器列表

    Args:
        adapter_type: 适配器类型过滤
        adapter_status: 状态过滤

    Returns:
        适配器列表响应
    """
    filters = {}
    if adapter_type:
        filters["adapter_type"] = adapter_type
    if adapter_status:
        filters["status"] = adapter_status

    adapters = await _adapter_service.list_adapters(filters)

    return AdapterListResponse(
        items=[_to_adapter_response(adapter) for _, adapter in adapters],
    )


@router.get(
    "/adapters/{adapter_id}",
    response_model=AdapterResponse,
    summary="获取适配器详情",
    description="根据ID获取适配器的详细信息",
)
async def get_adapter(adapter_id: str) -> AdapterResponse:
    """获取适配器详情

    Args:
        adapter_id: 适配器标识

    Returns:
        适配器响应

    Raises:
        HTTPException: 适配器不存在
    """
    try:
        adapter = await _adapter_service.get_adapter(adapter_id)
        return _to_adapter_response(adapter)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# Agent调用端点
# =============================================================================


@router.post(
    "/invoke",
    response_model=InvocationResponse,
    status_code=status.HTTP_200_OK,
    summary="调用Agent",
    description="通过指定适配器调用Agent执行任务",
)
async def invoke_agent(request: InvokeAgentRequest) -> InvocationResponse:
    """调用Agent

    Args:
        request: 调用Agent请求

    Returns:
        调用记录响应

    Raises:
        HTTPException: 调用失败
    """
    try:
        invocation = await _adapter_service.invoke_agent(
            adapter_id=request.adapter_id,
            agent_id=request.agent_id,
            input_data=request.input_data,
            config=request.config,
            operator=request.operator,
        )

        return _to_invocation_response(invocation)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 调用记录查询端点
# =============================================================================


@router.get(
    "/invocations/{invocation_id}",
    response_model=InvocationResponse,
    summary="获取调用记录详情",
    description="根据ID获取调用记录的详细信息",
)
async def get_invocation(invocation_id: str) -> InvocationResponse:
    """获取调用记录详情

    Args:
        invocation_id: 调用记录标识

    Returns:
        调用记录响应

    Raises:
        HTTPException: 调用记录不存在
    """
    try:
        invocation = await _adapter_service.get_invocation(invocation_id)
        return _to_invocation_response(invocation)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/invocations",
    response_model=InvocationListResponse,
    summary="查询调用记录列表",
    description="分页查询调用记录列表",
)
async def list_invocations(
    agent_id: str | None = Query(default=None, description="Agent标识过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> InvocationListResponse:
    """查询调用记录列表

    Args:
        agent_id: Agent标识过滤
        page: 页码
        page_size: 每页大小

    Returns:
        调用记录列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _adapter_service.list_invocations(
        agent_id=agent_id,
        pagination=pagination,
    )

    return InvocationListResponse(
        items=[_to_invocation_response(inv) for inv in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 健康检查端点
# =============================================================================


@router.post(
    "/adapters/{adapter_id}/health-check",
    status_code=status.HTTP_200_OK,
    summary="适配器健康检查",
    description="检查指定适配器的健康状态",
)
async def health_check(adapter_id: str) -> dict[str, bool]:
    """适配器健康检查

    Args:
        adapter_id: 适配器标识

    Returns:
        健康检查结果

    Raises:
        HTTPException: 适配器不存在
    """
    try:
        is_healthy = await _adapter_service.check_health(adapter_id)
        return {"healthy": is_healthy}

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 辅助函数
# =============================================================================


def _to_adapter_response(adapter: AgentAdapter) -> AdapterResponse:
    """将适配器实例转换为响应Schema

    Args:
        adapter: 适配器实例

    Returns:
        适配器响应
    """
    return AdapterResponse(
        id=adapter.id,
        adapter_type=adapter.adapter_type,
        status=adapter.status,
        config=adapter.config,
    )


def _to_invocation_response(invocation: AdapterInvocation) -> InvocationResponse:
    """将调用记录转换为响应Schema

    Args:
        invocation: 调用记录实体

    Returns:
        调用记录响应
    """
    return InvocationResponse(
        id=invocation.id,
        adapter_type=invocation.adapter_type,
        agent_id=invocation.agent_id,
        input_data=invocation.input_data,
        output_data=invocation.output_data,
        status=invocation.status,
        started_at=invocation.started_at,
        completed_at=invocation.completed_at,
        error_message=invocation.error_message,
        latency_ms=invocation.latency_ms,
        token_usage=invocation.token_usage,
        created_at=invocation.created_at,
        updated_at=invocation.updated_at,
        tenant_id=invocation.tenant_id,
    )
