"""
记忆路由

提供记忆的存储、检索、整合和管理功能。
"""

from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/memory", tags=["记忆"])


# ==================== 枚举定义 ====================

class MemoryType(str, Enum):
    """记忆类型枚举"""
    SHORT_TERM = "short_term"  # 短期记忆
    LONG_TERM = "long_term"  # 长期记忆
    EPISODIC = "episodic"  # 情景记忆
    SEMANTIC = "semantic"  # 语义记忆
    PROCEDURAL = "procedural"  # 程序记忆


class MemoryStatus(str, Enum):
    """记忆状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CONSOLIDATED = "consolidated"


# ==================== 请求/响应模型 ====================

class MemoryStoreRequest(BaseModel):
    """存储记忆请求"""
    key: str = Field(min_length=1, max_length=200, description="记忆键")
    value: Any = Field(description="记忆值")
    memory_type: MemoryType = Field(default=MemoryType.SHORT_TERM, description="记忆类型")
    metadata: dict = Field(default_factory=dict, description="元数据")
    ttl: Optional[int] = Field(default=None, ge=0, description="过期时间（秒），None表示永不过期")


class MemoryRecallRequest(BaseModel):
    """检索记忆请求"""
    query: str = Field(min_length=1, description="检索查询")
    memory_types: Optional[list[MemoryType]] = Field(default=None, description="限定的记忆类型")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="相似度阈值")


class MemoryItem(BaseModel):
    """记忆条目"""
    key: str = Field(description="记忆键")
    value: Any = Field(description="记忆值")
    memory_type: MemoryType = Field(description="记忆类型")
    metadata: dict = Field(description="元数据")
    score: Optional[float] = Field(description="相似度分数")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")


class MemoryRecallResponse(BaseModel):
    """检索记忆响应"""
    results: list[MemoryItem] = Field(description="检索结果列表")
    sources: list[str] = Field(description="来源记忆键列表")
    total: int = Field(description="结果总数")


class MemoryStatsResponse(BaseModel):
    """记忆统计响应"""
    total_memories: int = Field(description="记忆总数")
    by_type: dict[str, int] = Field(description="按类型统计")
    storage_size_bytes: int = Field(description="存储大小（字节）")


class EventReplayRequest(BaseModel):
    """事件回放请求"""
    event_type: Optional[str] = Field(default=None, description="事件类型过滤")
    start_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")


# ==================== 模拟数据存储 ====================
# TODO: 替换为实际的向量数据库或记忆服务

_memory_store: dict[str, MemoryItem] = {}
_event_log: list[dict] = []


# ==================== 路由处理函数 ====================

@router.post(
    "/memory/store",
    response_model=MemoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="存储记忆",
    description="存储一条新的记忆",
)
async def store_memory(
    request: MemoryStoreRequest,
    current_user: dict = Depends(get_current_user),
) -> MemoryItem:
    """存储记忆

    Args:
        request: 存储记忆请求
        current_user: 当前认证用户

    Returns:
        存储的记忆条目
    """
    from datetime import datetime

    now = datetime.utcnow().isoformat()

    # 如果键已存在，更新记忆
    existing = _memory_store.get(request.key)
    if existing:
        existing.value = request.value
        existing.memory_type = request.memory_type
        existing.metadata = request.metadata
        existing.updated_at = now
        return existing

    # 创建新的记忆条目
    memory = MemoryItem(
        key=request.key,
        value=request.value,
        memory_type=request.memory_type,
        metadata=request.metadata,
        score=None,
        created_at=now,
        updated_at=now,
    )

    _memory_store[request.key] = memory

    # 记录事件
    _event_log.append({
        "event_type": "memory_store",
        "key": request.key,
        "timestamp": now,
    })

    return memory


@router.post(
    "/memory/recall",
    response_model=MemoryRecallResponse,
    summary="检索记忆",
    description="根据查询检索相关记忆",
)
async def recall_memory(
    request: MemoryRecallRequest,
    current_user: dict = Depends(get_current_user),
) -> MemoryRecallResponse:
    """检索记忆

    Args:
        request: 检索记忆请求
        current_user: 当前认证用户

    Returns:
        检索结果
    """
    results = list(_memory_store.values())

    # 应用类型过滤
    if request.memory_types:
        results = [m for m in results if m.memory_type in request.memory_types]

    # 简单的关键词匹配（实际应使用向量相似度搜索）
    query_lower = request.query.lower()
    scored_results = []
    for memory in results:
        # 简单计算匹配分数
        value_str = str(memory.value).lower()
        key_str = memory.key.lower()
        if query_lower in value_str or query_lower in key_str:
            score = 0.8  # 模拟相似度分数
            memory_copy = memory.model_copy()
            memory_copy.score = score
            scored_results.append(memory_copy)

    # 按分数排序并限制数量
    scored_results.sort(key=lambda x: x.score or 0, reverse=True)
    scored_results = scored_results[:request.top_k]

    # 提取来源
    sources = [m.key for m in scored_results]

    return MemoryRecallResponse(
        results=scored_results,
        sources=sources,
        total=len(scored_results),
    )


@router.delete(
    "/memory/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除记忆",
    description="根据键删除指定记忆",
)
async def delete_memory(
    key: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """删除记忆

    Args:
        key: 记忆键
        current_user: 当前认证用户

    Raises:
        HTTPException: 记忆不存在
    """
    if key not in _memory_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆不存在: {key}",
        )

    del _memory_store[key]

    # 记录事件
    from datetime import datetime
    _event_log.append({
        "event_type": "memory_delete",
        "key": key,
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.post(
    "/memory/consolidate",
    summary="整合记忆",
    description="将短期记忆整合为长期记忆",
)
async def consolidate_memory(
    memory_types: Optional[list[MemoryType]] = Query(
        default=None,
        description="要整合的记忆类型",
    ),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """整合记忆

    将指定类型的短期记忆整合为长期记忆。

    Args:
        memory_types: 要整合的记忆类型，默认整合短期记忆
        current_user: 当前认证用户

    Returns:
        整合结果
    """
    from datetime import datetime

    # 默认整合短期记忆
    target_types = memory_types or [MemoryType.SHORT_TERM]
    consolidated_count = 0

    for memory in _memory_store.values():
        if memory.memory_type in target_types:
            memory.memory_type = MemoryType.LONG_TERM
            memory.metadata["consolidated_at"] = datetime.utcnow().isoformat()
            memory.updated_at = datetime.utcnow().isoformat()
            consolidated_count += 1

    # 记录事件
    _event_log.append({
        "event_type": "memory_consolidate",
        "types": [t.value for t in target_types],
        "count": consolidated_count,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "message": "记忆整合完成",
        "consolidated_count": consolidated_count,
    }


@router.get(
    "/memory/stats",
    response_model=MemoryStatsResponse,
    summary="获取记忆统计",
    description="获取记忆系统的统计信息",
)
async def get_memory_stats(
    current_user: dict = Depends(get_current_user),
) -> MemoryStatsResponse:
    """获取记忆统计

    Args:
        current_user: 当前认证用户

    Returns:
        记忆统计信息
    """
    import sys

    # 按类型统计
    by_type: dict[str, int] = {}
    for memory in _memory_store.values():
        type_name = memory.memory_type.value
        by_type[type_name] = by_type.get(type_name, 0) + 1

    # 估算存储大小
    storage_size = sys.getsizeof(str(_memory_store))

    return MemoryStatsResponse(
        total_memories=len(_memory_store),
        by_type=by_type,
        storage_size_bytes=storage_size,
    )


@router.post(
    "/memory/events/replay",
    summary="事件回放",
    description="回放记忆系统的事件日志",
)
async def replay_events(
    request: EventReplayRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """事件回放

    Args:
        request: 事件回放请求
        current_user: 当前认证用户

    Returns:
        事件列表
    """
    events = _event_log.copy()

    # 应用事件类型过滤
    if request.event_type:
        events = [e for e in events if e.get("event_type") == request.event_type]

    # 应用时间过滤
    if request.start_time:
        events = [e for e in events if e.get("timestamp", "") >= request.start_time]
    if request.end_time:
        events = [e for e in events if e.get("timestamp", "") <= request.end_time]

    # 限制数量
    events = events[:request.limit]

    return {
        "events": events,
        "total": len(events),
    }
