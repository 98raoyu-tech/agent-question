"""
工作流路由

提供工作流的创建、查询、执行和管理功能。
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/workflows", tags=["工作流"])


# ==================== 枚举定义 ====================

class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== 请求/响应模型 ====================

class WorkflowStep(BaseModel):
    """工作流步骤定义"""
    step_id: str = Field(description="步骤ID")
    name: str = Field(description="步骤名称")
    agent_type: str = Field(description="执行的Agent类型")
    config: dict = Field(default_factory=dict, description="步骤配置")
    dependencies: list[str] = Field(default_factory=list, description="依赖的步骤ID列表")


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(default=None, max_length=500, description="工作流描述")
    steps: list[WorkflowStep] = Field(min_length=1, description="工作流步骤列表")
    timeout: int = Field(default=3600, ge=1, le=86400, description="超时时间（秒）")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str = Field(description="工作流ID")
    name: str = Field(description="工作流名称")
    description: Optional[str] = Field(description="工作流描述")
    status: WorkflowStatus = Field(description="工作流状态")
    steps: list[WorkflowStep] = Field(description="工作流步骤列表")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")


class ExecutionResponse(BaseModel):
    """执行状态响应"""
    execution_id: str = Field(description="执行ID")
    workflow_id: str = Field(description="工作流ID")
    status: ExecutionStatus = Field(description="执行状态")
    current_step: Optional[str] = Field(description="当前执行步骤")
    progress: float = Field(ge=0, le=100, description="执行进度百分比")
    started_at: Optional[str] = Field(description="开始时间")
    completed_at: Optional[str] = Field(description="完成时间")
    error: Optional[str] = Field(description="错误信息")


# ==================== 模拟数据存储 ====================
# TODO: 替换为实际的数据库或服务调用

_workflow_store: dict[str, WorkflowResponse] = {}
_execution_store: dict[str, ExecutionResponse] = {}


# ==================== 路由处理函数 ====================

@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建工作流",
    description="创建一个新的工作流定义",
)
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> WorkflowResponse:
    """创建并启动工作流

    Args:
        request: 工作流创建请求
        current_user: 当前认证用户

    Returns:
        创建的工作流信息
    """
    import uuid
    from datetime import datetime

    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    workflow = WorkflowResponse(
        workflow_id=workflow_id,
        name=request.name,
        description=request.description,
        status=WorkflowStatus.DRAFT,
        steps=request.steps,
        created_at=now,
        updated_at=now,
    )

    _workflow_store[workflow_id] = workflow
    return workflow


@router.get(
    "/workflows",
    summary="列出工作流",
    description="获取所有工作流定义列表",
)
async def list_workflows(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[WorkflowStatus] = Query(default=None, alias="status", description="状态过滤"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """列出工作流定义

    Args:
        page: 页码
        page_size: 每页大小
        status_filter: 状态过滤条件
        current_user: 当前认证用户

    Returns:
        分页的工作流列表
    """
    workflows = list(_workflow_store.values())

    # 应用状态过滤
    if status_filter:
        workflows = [w for w in workflows if w.status == status_filter]

    # 计算分页
    total = len(workflows)
    start = (page - 1) * page_size
    end = start + page_size
    items = [w.model_dump() for w in workflows[start:end]]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    summary="获取工作流详情",
    description="根据ID获取工作流详细信息",
)
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
) -> WorkflowResponse:
    """获取工作流详情

    Args:
        workflow_id: 工作流ID
        current_user: 当前认证用户

    Returns:
        工作流详细信息

    Raises:
        HTTPException: 工作流不存在
    """
    workflow = _workflow_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )
    return workflow


@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=ExecutionResponse,
    summary="执行工作流",
    description="启动指定工作流的执行",
)
async def execute_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
) -> ExecutionResponse:
    """执行工作流

    Args:
        workflow_id: 工作流ID
        current_user: 当前认证用户

    Returns:
        执行状态信息

    Raises:
        HTTPException: 工作流不存在或状态不允许执行
    """
    import uuid
    from datetime import datetime

    workflow = _workflow_store.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_id}",
        )

    # 检查工作流状态是否允许执行
    if workflow.status not in [WorkflowStatus.DRAFT, WorkflowStatus.ACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工作流状态不允许执行: {workflow.status.value}",
        )

    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    execution = ExecutionResponse(
        execution_id=execution_id,
        workflow_id=workflow_id,
        status=ExecutionStatus.RUNNING,
        current_step=workflow.steps[0].step_id if workflow.steps else None,
        progress=0.0,
        started_at=now,
        completed_at=None,
        error=None,
    )

    _execution_store[execution_id] = execution
    return execution


@router.get(
    "/workflows/executions/{execution_id}",
    response_model=ExecutionResponse,
    summary="获取执行状态",
    description="根据执行ID获取执行状态",
)
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
) -> ExecutionResponse:
    """获取执行状态

    Args:
        execution_id: 执行ID
        current_user: 当前认证用户

    Returns:
        执行状态信息

    Raises:
        HTTPException: 执行记录不存在
    """
    execution = _execution_store.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录不存在: {execution_id}",
        )
    return execution


@router.post(
    "/workflows/executions/{execution_id}/pause",
    response_model=ExecutionResponse,
    summary="暂停执行",
    description="暂停正在运行的工作流执行",
)
async def pause_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
) -> ExecutionResponse:
    """暂停执行

    Args:
        execution_id: 执行ID
        current_user: 当前认证用户

    Returns:
        更新后的执行状态

    Raises:
        HTTPException: 执行记录不存在或状态不允许暂停
    """
    execution = _execution_store.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录不存在: {execution_id}",
        )

    if execution.status != ExecutionStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"执行状态不允许暂停: {execution.status.value}",
        )

    execution.status = ExecutionStatus.PAUSED
    return execution


@router.post(
    "/workflows/executions/{execution_id}/resume",
    response_model=ExecutionResponse,
    summary="恢复执行",
    description="恢复已暂停的工作流执行",
)
async def resume_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
) -> ExecutionResponse:
    """恢复执行

    Args:
        execution_id: 执行ID
        current_user: 当前认证用户

    Returns:
        更新后的执行状态

    Raises:
        HTTPException: 执行记录不存在或状态不允许恢复
    """
    execution = _execution_store.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录不存在: {execution_id}",
        )

    if execution.status != ExecutionStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"执行状态不允许恢复: {execution.status.value}",
        )

    execution.status = ExecutionStatus.RUNNING
    return execution


@router.post(
    "/workflows/executions/{execution_id}/cancel",
    response_model=ExecutionResponse,
    summary="取消执行",
    description="取消正在运行或已暂停的工作流执行",
)
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
) -> ExecutionResponse:
    """取消执行

    Args:
        execution_id: 执行ID
        current_user: 当前认证用户

    Returns:
        更新后的执行状态

    Raises:
        HTTPException: 执行记录不存在或状态不允许取消
    """
    execution = _execution_store.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录不存在: {execution_id}",
        )

    # 只有运行中或暂停的执行可以取消
    if execution.status not in [ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"执行状态不允许取消: {execution.status.value}",
        )

    execution.status = ExecutionStatus.CANCELLED
    return execution
