"""
审核路由

提供任务审核的查询、批准和拒绝功能。
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/approvals", tags=["审核"])


# ==================== 枚举定义 ====================

class ApprovalStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(str, Enum):
    """审核类型枚举"""
    WORKFLOW = "workflow"  # 工作流审核
    TOOL_INVOCATION = "tool_invocation"  # 工具调用审核
    DATA_ACCESS = "data_access"  # 数据访问审核
    AGENT_ACTION = "agent_action"  # Agent操作审核


# ==================== 请求/响应模型 ====================

class ApprovalRequest(BaseModel):
    """审核请求"""
    request_id: str = Field(description="请求ID")
    approval_type: ApprovalType = Field(description="审核类型")
    status: ApprovalStatus = Field(description="审核状态")
    requester: str = Field(description="请求者")
    description: str = Field(description="请求描述")
    context: dict = Field(default_factory=dict, description="请求上下文")
    created_at: str = Field(description="创建时间")
    expires_at: Optional[str] = Field(description="过期时间")
    reviewed_by: Optional[str] = Field(description="审核人")
    reviewed_at: Optional[str] = Field(description="审核时间")
    review_comment: Optional[str] = Field(description="审核意见")


class ApprovalActionRequest(BaseModel):
    """审核操作请求"""
    comment: Optional[str] = Field(default=None, max_length=500, description="审核意见")


# ==================== 模拟数据存储 ====================
# TODO: 替换为实际的审核服务

_approval_store: dict[str, ApprovalRequest] = {}


def _init_mock_data() -> None:
    """初始化模拟数据"""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    mock_approvals = [
        ApprovalRequest(
            request_id="approval_001",
            approval_type=ApprovalType.WORKFLOW,
            status=ApprovalStatus.PENDING,
            requester="user_001",
            description="执行数据处理工作流",
            context={"workflow_id": "wf_001", "workflow_name": "数据清洗"},
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=24)).isoformat(),
            reviewed_by=None,
            reviewed_at=None,
            review_comment=None,
        ),
        ApprovalRequest(
            request_id="approval_002",
            approval_type=ApprovalType.TOOL_INVOCATION,
            status=ApprovalStatus.PENDING,
            requester="agent_001",
            description="调用外部API获取数据",
            context={"tool_name": "web_search", "query": "AI最新进展"},
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=1)).isoformat(),
            reviewed_by=None,
            reviewed_at=None,
            review_comment=None,
        ),
        ApprovalRequest(
            request_id="approval_003",
            approval_type=ApprovalType.DATA_ACCESS,
            status=ApprovalStatus.APPROVED,
            requester="user_002",
            description="访问用户敏感数据",
            context={"data_type": "user_profile", "scope": "read"},
            created_at=(now - timedelta(hours=2)).isoformat(),
            expires_at=(now + timedelta(hours=22)).isoformat(),
            reviewed_by="admin_001",
            reviewed_at=(now - timedelta(hours=1)).isoformat(),
            review_comment="已验证用户权限",
        ),
    ]

    for approval in mock_approvals:
        _approval_store[approval.request_id] = approval


# 初始化模拟数据
_init_mock_data()


# ==================== 路由处理函数 ====================

@router.get(
    "/approvals",
    summary="获取待审核列表",
    description="获取待审核的请求列表",
)
async def list_approvals(
    status_filter: Optional[ApprovalStatus] = Query(default=None, alias="status", description="状态过滤"),
    approval_type: Optional[ApprovalType] = Query(default=None, description="类型过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取待审核列表

    Args:
        status_filter: 状态过滤条件
        approval_type: 类型过滤条件
        page: 页码
        page_size: 每页大小
        current_user: 当前认证用户

    Returns:
        分页的审核请求列表
    """
    approvals = list(_approval_store.values())

    # 应用过滤条件
    if status_filter:
        approvals = [a for a in approvals if a.status == status_filter]
    if approval_type:
        approvals = [a for a in approvals if a.approval_type == approval_type]

    # 按创建时间倒序排序
    approvals.sort(key=lambda x: x.created_at, reverse=True)

    # 计算分页
    total = len(approvals)
    start = (page - 1) * page_size
    end = start + page_size
    items = [a.model_dump() for a in approvals[start:end]]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/approvals/{request_id}",
    response_model=ApprovalRequest,
    summary="获取审核详情",
    description="根据请求ID获取审核详细信息",
)
async def get_approval(
    request_id: str,
    current_user: dict = Depends(get_current_user),
) -> ApprovalRequest:
    """获取审核详情

    Args:
        request_id: 请求ID
        current_user: 当前认证用户

    Returns:
        审核请求详细信息

    Raises:
        HTTPException: 审核请求不存在
    """
    approval = _approval_store.get(request_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"审核请求不存在: {request_id}",
        )
    return approval


@router.post(
    "/approvals/{request_id}/approve",
    response_model=ApprovalRequest,
    summary="审核通过",
    description="批准指定的审核请求",
)
async def approve_request(
    request_id: str,
    action: ApprovalActionRequest = ApprovalActionRequest(),
    current_user: dict = Depends(get_current_user),
) -> ApprovalRequest:
    """审核通过

    Args:
        request_id: 请求ID
        action: 审核操作请求
        current_user: 当前认证用户

    Returns:
        更新后的审核请求

    Raises:
        HTTPException: 审核请求不存在或状态不允许操作
    """
    from datetime import datetime

    approval = _approval_store.get(request_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"审核请求不存在: {request_id}",
        )

    # 检查状态是否允许操作
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"审核请求状态不允许操作: {approval.status.value}",
        )

    # 获取当前用户ID
    user_id = current_user.get("sub", "unknown")

    # 更新审核状态
    approval.status = ApprovalStatus.APPROVED
    approval.reviewed_by = user_id
    approval.reviewed_at = datetime.utcnow().isoformat()
    approval.review_comment = action.comment

    return approval


@router.post(
    "/approvals/{request_id}/reject",
    response_model=ApprovalRequest,
    summary="审核拒绝",
    description="拒绝指定的审核请求",
)
async def reject_request(
    request_id: str,
    action: ApprovalActionRequest = ApprovalActionRequest(),
    current_user: dict = Depends(get_current_user),
) -> ApprovalRequest:
    """审核拒绝

    Args:
        request_id: 请求ID
        action: 审核操作请求
        current_user: 当前认证用户

    Returns:
        更新后的审核请求

    Raises:
        HTTPException: 审核请求不存在或状态不允许操作
    """
    from datetime import datetime

    approval = _approval_store.get(request_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"审核请求不存在: {request_id}",
        )

    # 检查状态是否允许操作
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"审核请求状态不允许操作: {approval.status.value}",
        )

    # 获取当前用户ID
    user_id = current_user.get("sub", "unknown")

    # 更新审核状态
    approval.status = ApprovalStatus.REJECTED
    approval.reviewed_by = user_id
    approval.reviewed_at = datetime.utcnow().isoformat()
    approval.review_comment = action.comment

    return approval
