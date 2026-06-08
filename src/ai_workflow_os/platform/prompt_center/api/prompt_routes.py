"""
Prompt中心 FastAPI路由

提供Prompt模板管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.prompt_service import PromptService
from ..domain.prompt_template import PromptTemplate
from ..domain.enums import PromptCategory
from ..infrastructure.prompt_repository import PromptRepository
from .schemas import (
    CreatePromptRequest,
    PromptListResponse,
    PromptResponse,
    UpdatePromptRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prompt-center", tags=["Prompt中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_prompt_repository = PromptRepository()
_prompt_service = PromptService(_prompt_repository)


@router.post(
    "/templates",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建Prompt模板",
    description="创建一个新的Prompt模板",
)
async def create_template(request: CreatePromptRequest) -> PromptResponse:
    """创建Prompt模板"""
    try:
        template = PromptTemplate(
            name=request.name,
            description=request.description,
            content=request.content,
            category=request.category,
            variables=request.variables,
            model_compatibility=request.model_compatibility,
            tags=request.tags,
            tenant_id=request.tenant_id,
        )

        created_template = await _prompt_service.create_template(template)

        return _to_prompt_response(created_template)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/templates/{template_id}",
    response_model=PromptResponse,
    summary="获取Prompt模板详情",
    description="根据ID获取Prompt模板的详细信息",
)
async def get_template(template_id: str) -> PromptResponse:
    """获取Prompt模板详情"""
    try:
        template = await _prompt_service.get_template(template_id)
        return _to_prompt_response(template)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/templates",
    response_model=PromptListResponse,
    summary="查询Prompt模板列表",
    description="分页查询Prompt模板列表",
)
async def list_templates(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> PromptListResponse:
    """查询Prompt模板列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _prompt_service.list_templates(pagination, tenant_id)

    return PromptListResponse(
        items=[_to_prompt_response(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.put(
    "/templates/{template_id}",
    response_model=PromptResponse,
    summary="更新Prompt模板",
    description="更新Prompt模板信息",
)
async def update_template(template_id: str, request: UpdatePromptRequest) -> PromptResponse:
    """更新Prompt模板"""
    try:
        existing = await _prompt_service.get_template(template_id)

        if request.name is not None:
            existing.name = request.name
        if request.description is not None:
            existing.description = request.description
        if request.content is not None:
            existing.content = request.content
        if request.category is not None:
            existing.category = request.category
        if request.variables is not None:
            existing.variables = request.variables
        if request.model_compatibility is not None:
            existing.model_compatibility = request.model_compatibility
        if request.tags is not None:
            existing.tags = request.tags

        updated_template = await _prompt_service.update_template(template_id, existing)

        return _to_prompt_response(updated_template)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除Prompt模板",
    description="软删除Prompt模板",
)
async def delete_template(template_id: str) -> None:
    """删除Prompt模板"""
    try:
        await _prompt_service.delete_template(template_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


def _to_prompt_response(template: PromptTemplate) -> PromptResponse:
    """将Prompt模板实体转换为响应Schema"""
    return PromptResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        content=template.content,
        category=template.category,
        status=template.status,
        variables=template.variables,
        model_compatibility=template.model_compatibility,
        usage_count=template.usage_count,
        tags=template.tags,
        created_at=template.created_at,
        updated_at=template.updated_at,
        tenant_id=template.tenant_id,
    )
