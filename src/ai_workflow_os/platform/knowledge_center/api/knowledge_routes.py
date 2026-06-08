"""
知识中心 FastAPI路由

提供知识源和文档管理的RESTful API端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import PlatformException, ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest
from ..application.knowledge_service import KnowledgeService
from ..domain.knowledge_document import KnowledgeDocument
from ..domain.knowledge_source import KnowledgeSource
from ..domain.enums import SourceType
from ..infrastructure.knowledge_repository import KnowledgeRepository
from .schemas import (
    CreateDocumentRequest,
    CreateSourceRequest,
    DocumentListResponse,
    DocumentResponse,
    SourceListResponse,
    SourceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-center", tags=["知识中心"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_knowledge_repository = KnowledgeRepository()
_knowledge_service = KnowledgeService(_knowledge_repository)


# =============================================================================
# 知识源端点
# =============================================================================


@router.post(
    "/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建知识源",
    description="创建一个新的知识源",
)
async def create_source(request: CreateSourceRequest) -> SourceResponse:
    """创建知识源

    Args:
        request: 创建知识源请求

    Returns:
        创建的知识源响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        source = KnowledgeSource(
            name=request.name,
            description=request.description,
            source_type=request.source_type,
            config=request.config,
            tags=request.tags,
            tenant_id=request.tenant_id,
        )

        created_source = await _knowledge_service.create_source(source)

        return _to_source_response(created_source)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sources/{source_id}",
    response_model=SourceResponse,
    summary="获取知识源详情",
    description="根据ID获取知识源的详细信息",
)
async def get_source(source_id: str) -> SourceResponse:
    """获取知识源详情

    Args:
        source_id: 知识源标识

    Returns:
        知识源响应

    Raises:
        HTTPException: 知识源不存在
    """
    try:
        source = await _knowledge_service.get_source(source_id)
        return _to_source_response(source)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sources",
    response_model=SourceListResponse,
    summary="查询知识源列表",
    description="分页查询知识源列表",
)
async def list_sources(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: Optional[str] = Query(default=None, description="租户标识"),
) -> SourceListResponse:
    """查询知识源列表

    Args:
        page: 页码
        page_size: 每页大小
        tenant_id: 租户标识

    Returns:
        知识源列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _knowledge_service.list_sources(pagination, tenant_id)

    return SourceListResponse(
        items=[_to_source_response(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识源",
    description="软删除知识源",
)
async def delete_source(source_id: str) -> None:
    """删除知识源

    Args:
        source_id: 知识源标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _knowledge_service.delete_source(source_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 文档端点
# =============================================================================


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建文档",
    description="在知识源下创建一个新文档",
)
async def create_document(request: CreateDocumentRequest) -> DocumentResponse:
    """创建文档

    Args:
        request: 创建文档请求

    Returns:
        创建的文档响应

    Raises:
        HTTPException: 创建失败
    """
    try:
        document = KnowledgeDocument(
            source_id=request.source_id,
            title=request.title,
            content=request.content,
            file_path=request.file_path,
            file_size=request.file_size,
            file_type=request.file_type,
            metadata=request.metadata,
            tenant_id=request.tenant_id,
        )

        created_document = await _knowledge_service.create_document(document)

        return _to_document_response(created_document)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="获取文档详情",
    description="根据ID获取文档的详细信息",
)
async def get_document(document_id: str) -> DocumentResponse:
    """获取文档详情

    Args:
        document_id: 文档标识

    Returns:
        文档响应

    Raises:
        HTTPException: 文档不存在
    """
    try:
        document = await _knowledge_service.get_document(document_id)
        return _to_document_response(document)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/sources/{source_id}/documents",
    response_model=DocumentListResponse,
    summary="查询文档列表",
    description="查询知识源下的文档列表",
)
async def list_documents(
    source_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> DocumentListResponse:
    """查询文档列表

    Args:
        source_id: 知识源标识
        page: 页码
        page_size: 每页大小

    Returns:
        文档列表响应
    """
    pagination = PaginatedRequest(page=page, page_size=page_size)
    result = await _knowledge_service.list_documents(source_id, pagination)

    return DocumentListResponse(
        items=[_to_document_response(d) for d in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文档",
    description="软删除文档",
)
async def delete_document(document_id: str) -> None:
    """删除文档

    Args:
        document_id: 文档标识

    Raises:
        HTTPException: 删除失败
    """
    try:
        await _knowledge_service.delete_document(document_id)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_source_response(source: KnowledgeSource) -> SourceResponse:
    """将知识源实体转换为响应Schema

    Args:
        source: 知识源实体

    Returns:
        知识源响应
    """
    return SourceResponse(
        id=source.id,
        name=source.name,
        description=source.description,
        source_type=source.source_type,
        document_count=source.document_count,
        total_chunks=source.total_chunks,
        is_enabled=source.is_enabled,
        tags=source.tags,
        created_at=source.created_at,
        updated_at=source.updated_at,
        tenant_id=source.tenant_id,
    )


def _to_document_response(document: KnowledgeDocument) -> DocumentResponse:
    """将文档实体转换为响应Schema

    Args:
        document: 文档实体

    Returns:
        文档响应
    """
    return DocumentResponse(
        id=document.id,
        source_id=document.source_id,
        title=document.title,
        content=document.content[:500] if document.content else "",
        file_path=document.file_path,
        file_size=document.file_size,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
        tenant_id=document.tenant_id,
    )
