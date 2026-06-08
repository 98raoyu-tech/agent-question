"""
工具市场 FastAPI路由

提供工具定义管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.tool_service import ToolService
from ..domain.tool_definition import ToolDefinition
from ..domain.enums import ToolType
from ..infrastructure.tool_repository import ToolRepository
from .schemas import (
    CreateToolRequest,
    ToolListResponse,
    ToolResponse,
    UpdateToolRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tool-marketplace", tags=["工具市场"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_tool_repository = ToolRepository()
_tool_service = ToolService(_tool_repository)


@router.post(
    "/tools",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建工具定义",
    description="创建一个新的工具定义",
)
async def create_tool(request: CreateToolRequest) -> ToolResponse:
    """创建工具定义"""
    try:
        tool = ToolDefinition(
            name=request.name,
            description=request.description,
            tool_type=request.tool_type,
            endpoint=request.endpoint,
            parameters=request.parameters,
            return_type=request.return_type,
            authentication=request.authentication,
            timeout=request.timeout,
            retry_count=request.retry_count,
            author=request.author,
            version=request.version,
            tags=request.tags,
            tenant_id=request.tenant_id,
        )

        created_tool = await _tool_service.create_tool(tool)

        return _to_tool_response(created_tool)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    summary="获取工具详情",
    description="根据ID获取工具的详细信息",
)
async def get_tool(tool_id: str) -> ToolResponse:
    """获取工具详情"""
    try:
        tool = await _tool_service.get_tool(tool_id)
        return _to_tool_response(tool)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/tools",
    response_model=ToolListResponse,
    summary="查询工具列表",
    description="分页查询工具列表",
)
async def list_tools(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> ToolListResponse:
    """查询工具列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _tool_service.list_tools(pagination, tenant_id)

    return ToolListResponse(
        items=[_to_tool_response(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    summary="更新工具定义",
    description="更新工具定义信息",
)
async def update_tool(tool_id: str, request: UpdateToolRequest) -> ToolResponse:
    """更新工具定义"""
    try:
        existing = await _tool_service.get_tool(tool_id)

        if request.name is not None:
            existing.name = request.name
        if request.description is not None:
            existing.description = request.description
        if request.tool_type is not None:
            existing.tool_type = request.tool_type
        if request.endpoint is not None:
            existing.endpoint = request.endpoint
        if request.parameters is not None:
            existing.parameters = request.parameters
        if request.return_type is not None:
            existing.return_type = request.return_type
        if request.authentication is not None:
            existing.authentication = request.authentication
        if request.timeout is not None:
            existing.timeout = request.timeout
        if request.retry_count is not None:
            existing.retry_count = request.retry_count
        if request.author is not None:
            existing.author = request.author
        if request.tags is not None:
            existing.tags = request.tags

        updated_tool = await _tool_service.update_tool(tool_id, existing)

        return _to_tool_response(updated_tool)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除工具定义",
    description="软删除工具定义",
)
async def delete_tool(tool_id: str) -> None:
    """删除工具定义"""
    try:
        await _tool_service.delete_tool(tool_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


def _to_tool_response(tool: ToolDefinition) -> ToolResponse:
    """将工具实体转换为响应Schema"""
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        status=tool.status,
        endpoint=tool.endpoint,
        parameters=tool.parameters,
        return_type=tool.return_type,
        timeout=tool.timeout,
        retry_count=tool.retry_count,
        usage_count=tool.usage_count,
        author=tool.author,
        version=tool.version,
        tags=tool.tags,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
        tenant_id=tool.tenant_id,
    )
