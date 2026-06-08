"""
Agent路由

提供Agent集群的任务分派、状态查询和管理功能。
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["Agent"])


# ==================== 枚举定义 ====================

class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    OFFLINE = "offline"
    ERROR = "error"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== 请求/响应模型 ====================

class TaskDispatchRequest(BaseModel):
    """任务分派请求"""
    task_type: str = Field(min_length=1, description="任务类型")
    payload: dict = Field(default_factory=dict, description="任务负载数据")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="任务优先级")
    timeout: int = Field(default=300, ge=1, le=3600, description="超时时间（秒）")


class AgentResponse(BaseModel):
    """Agent响应"""
    agent_id: str = Field(description="Agent ID")
    agent_type: str = Field(description="Agent类型")
    status: AgentStatus = Field(description="Agent状态")
    current_task: Optional[str] = Field(description="当前执行的任务ID")
    capabilities: list[str] = Field(default_factory=list, description="Agent能力列表")
    last_active: Optional[str] = Field(description="最后活跃时间")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(description="任务ID")
    task_type: str = Field(description="任务类型")
    status: TaskStatus = Field(description="任务状态")
    assigned_agent: Optional[str] = Field(description="分配的Agent ID")
    priority: TaskPriority = Field(description="任务优先级")
    created_at: str = Field(description="创建时间")
    started_at: Optional[str] = Field(description="开始时间")
    completed_at: Optional[str] = Field(description="完成时间")
    result: Optional[dict] = Field(description="任务结果")
    error: Optional[str] = Field(description="错误信息")


class ClusterStatusResponse(BaseModel):
    """集群状态响应"""
    total_agents: int = Field(description="Agent总数")
    active_agents: int = Field(description="活跃Agent数")
    pending_tasks: int = Field(description="待处理任务数")
    task_queue_size: int = Field(description="任务队列大小")


# ==================== 模拟数据存储 ====================
# TODO: 替换为实际的Agent管理服务

_agent_store: dict[str, AgentResponse] = {}
_task_store: dict[str, TaskResponse] = {}
_task_queue: list[str] = []


# ==================== 路由处理函数 ====================

@router.post(
    "/agents/dispatch",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="分派任务",
    description="将任务分派到Agent集群",
)
async def dispatch_task(
    request: TaskDispatchRequest,
    current_user: dict = Depends(get_current_user),
) -> TaskResponse:
    """分派任务到Agent集群

    Args:
        request: 任务分派请求
        current_user: 当前认证用户

    Returns:
        创建的任务信息
    """
    import uuid
    from datetime import datetime

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    task = TaskResponse(
        task_id=task_id,
        task_type=request.task_type,
        status=TaskStatus.PENDING,
        assigned_agent=None,
        priority=request.priority,
        created_at=now,
        started_at=None,
        completed_at=None,
        result=None,
        error=None,
    )

    _task_store[task_id] = task
    _task_queue.append(task_id)

    return task


@router.get(
    "/agents",
    summary="列出Agent",
    description="获取所有活跃Agent列表",
)
async def list_agents(
    status_filter: Optional[AgentStatus] = Query(default=None, alias="status", description="状态过滤"),
    agent_type: Optional[str] = Query(default=None, description="Agent类型过滤"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """列出所有活跃Agent

    Args:
        status_filter: 状态过滤条件
        agent_type: Agent类型过滤
        current_user: 当前认证用户

    Returns:
        Agent列表
    """
    agents = list(_agent_store.values())

    # 应用过滤条件
    if status_filter:
        agents = [a for a in agents if a.status == status_filter]
    if agent_type:
        agents = [a for a in agents if a.agent_type == agent_type]

    return {
        "items": [a.model_dump() for a in agents],
        "total": len(agents),
    }


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="获取Agent状态",
    description="根据ID获取Agent详细状态",
)
async def get_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> AgentResponse:
    """获取Agent状态

    Args:
        agent_id: Agent ID
        current_user: 当前认证用户

    Returns:
        Agent详细状态

    Raises:
        HTTPException: Agent不存在
    """
    agent = _agent_store.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}",
        )
    return agent


@router.post(
    "/agents/{agent_id}/pause",
    response_model=AgentResponse,
    summary="暂停Agent",
    description="暂停指定Agent",
)
async def pause_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> AgentResponse:
    """暂停Agent

    Args:
        agent_id: Agent ID
        current_user: 当前认证用户

    Returns:
        更新后的Agent状态

    Raises:
        HTTPException: Agent不存在或状态不允许暂停
    """
    agent = _agent_store.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}",
        )

    if agent.status not in [AgentStatus.IDLE, AgentStatus.BUSY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent状态不允许暂停: {agent.status.value}",
        )

    agent.status = AgentStatus.PAUSED
    return agent


@router.post(
    "/agents/{agent_id}/resume",
    response_model=AgentResponse,
    summary="恢复Agent",
    description="恢复已暂停的Agent",
)
async def resume_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> AgentResponse:
    """恢复Agent

    Args:
        agent_id: Agent ID
        current_user: 当前认证用户

    Returns:
        更新后的Agent状态

    Raises:
        HTTPException: Agent不存在或状态不允许恢复
    """
    agent = _agent_store.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_id}",
        )

    if agent.status != AgentStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent状态不允许恢复: {agent.status.value}",
        )

    agent.status = AgentStatus.IDLE
    return agent


@router.get(
    "/agents/cluster/status",
    response_model=ClusterStatusResponse,
    summary="获取集群状态",
    description="获取Agent集群整体状态",
)
async def get_cluster_status(
    current_user: dict = Depends(get_current_user),
) -> ClusterStatusResponse:
    """获取集群状态

    Args:
        current_user: 当前认证用户

    Returns:
        集群状态信息
    """
    agents = list(_agent_store.values())
    active_agents = len([a for a in agents if a.status in [AgentStatus.IDLE, AgentStatus.BUSY]])
    pending_tasks = len([t for t in _task_store.values() if t.status == TaskStatus.PENDING])

    return ClusterStatusResponse(
        total_agents=len(agents),
        active_agents=active_agents,
        pending_tasks=pending_tasks,
        task_queue_size=len(_task_queue),
    )
