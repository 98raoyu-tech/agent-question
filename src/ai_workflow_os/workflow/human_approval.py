"""
人类审核管理

管理需要人类审核的工作流节点，支持审核请求、批准、拒绝和超时处理。
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional


# ==================== 枚举定义 ====================

class ApprovalStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==================== 数据类定义 ====================

@dataclass
class ApprovalRequest:
    """审核请求

    Attributes:
        request_id: 请求唯一标识
        execution_id: 关联的工作流执行ID
        step_id: 关联的步骤ID
        action_description: 需要审核的操作描述
        risk_level: 风险等级
        context: 上下文信息
        status: 审核状态
        created_at: 创建时间
        expires_at: 过期时间
        approver_id: 审核人ID
        comment: 审核意见
        completed_at: 完成时间
    """
    request_id: str = field(default_factory=lambda: f"approval_{uuid.uuid4().hex[:12]}")
    execution_id: str = ""
    step_id: str = ""
    action_description: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    context: dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    approver_id: Optional[str] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class ApprovalResult:
    """审核结果

    Attributes:
        request_id: 请求ID
        status: 审核状态
        approver_id: 审核人ID
        comment: 审核意见
        completed_at: 完成时间
    """
    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_id: Optional[str] = None
    comment: Optional[str] = None
    completed_at: Optional[datetime] = None


# ==================== 审核管理器 ====================

class HumanApprovalManager:
    """人类审核管理器

    管理需要人类审核的工作流节点，支持审核请求、批准、拒绝和超时处理。

    Attributes:
        pending_approvals: 待审核请求字典
        approval_timeout: 审核超时时间（秒）
    """

    def __init__(self, approval_timeout: int = 3600) -> None:
        """初始化审核管理器

        Args:
            approval_timeout: 审核超时时间（秒），默认1小时
        """
        self.pending_approvals: dict[str, ApprovalRequest] = {}
        self.approval_timeout: int = approval_timeout

    async def request_approval(
        self,
        execution_id: str,
        step_id: str,
        action_description: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """请求人类审核

        Args:
            execution_id: 工作流执行ID
            step_id: 步骤ID
            action_description: 操作描述
            risk_level: 风险等级
            context: 上下文信息

        Returns:
            审核请求ID
        """
        # 创建审核请求
        request = ApprovalRequest(
            execution_id=execution_id,
            step_id=step_id,
            action_description=action_description,
            risk_level=risk_level,
            context=context or {},
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.approval_timeout),
        )

        # 保存到待审核列表
        self.pending_approvals[request.request_id] = request

        # TODO: 发送审核通知（如邮件、Slack等）

        return request.request_id

    async def approve(
        self,
        request_id: str,
        approver_id: str,
        comment: str = "",
    ) -> None:
        """审核通过

        Args:
            request_id: 审核请求ID
            approver_id: 审核人ID
            comment: 审核意见

        Raises:
            ValueError: 请求不存在或状态不允许审核
        """
        if request_id not in self.pending_approvals:
            raise ValueError(f"审核请求不存在: {request_id}")

        request = self.pending_approvals[request_id]

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"审核请求状态不允许审核: {request.status.value}")

        # 检查是否已过期
        if self._is_expired(request):
            request.status = ApprovalStatus.EXPIRED
            raise ValueError("审核请求已过期")

        # 更新审核状态
        request.status = ApprovalStatus.APPROVED
        request.approver_id = approver_id
        request.comment = comment
        request.completed_at = datetime.now(timezone.utc)

    async def reject(
        self,
        request_id: str,
        approver_id: str,
        reason: str = "",
    ) -> None:
        """审核拒绝

        Args:
            request_id: 审核请求ID
            approver_id: 审核人ID
            reason: 拒绝原因

        Raises:
            ValueError: 请求不存在或状态不允许审核
        """
        if request_id not in self.pending_approvals:
            raise ValueError(f"审核请求不存在: {request_id}")

        request = self.pending_approvals[request_id]

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"审核请求状态不允许审核: {request.status.value}")

        # 检查是否已过期
        if self._is_expired(request):
            request.status = ApprovalStatus.EXPIRED
            raise ValueError("审核请求已过期")

        # 更新审核状态
        request.status = ApprovalStatus.REJECTED
        request.approver_id = approver_id
        request.comment = reason
        request.completed_at = datetime.now(timezone.utc)

    async def wait_for_approval(
        self,
        request_id: str,
        poll_interval: float = 1.0,
    ) -> ApprovalResult:
        """等待审核结果（带超时）

        Args:
            request_id: 审核请求ID
            poll_interval: 轮询间隔（秒）

        Returns:
            审核结果

        Raises:
            ValueError: 请求不存在
            TimeoutError: 审核超时
        """
        if request_id not in self.pending_approvals:
            raise ValueError(f"审核请求不存在: {request_id}")

        request = self.pending_approvals[request_id]

        # 轮询等待审核结果
        while request.status == ApprovalStatus.PENDING:
            # 检查是否已过期
            if self._is_expired(request):
                request.status = ApprovalStatus.EXPIRED
                break

            # 等待一段时间后再次检查
            await asyncio.sleep(poll_interval)

        # 返回审核结果
        return ApprovalResult(
            request_id=request.request_id,
            status=request.status,
            approver_id=request.approver_id,
            comment=request.comment,
            completed_at=request.completed_at,
        )

    def _check_timeout(self) -> list[str]:
        """检查超时请求

        Returns:
            超时的请求ID列表
        """
        expired_ids = []

        for request_id, request in self.pending_approvals.items():
            if request.status == ApprovalStatus.PENDING and self._is_expired(request):
                request.status = ApprovalStatus.EXPIRED
                expired_ids.append(request_id)

        return expired_ids

    def _is_expired(self, request: ApprovalRequest) -> bool:
        """检查请求是否已过期

        Args:
            request: 审核请求

        Returns:
            是否已过期
        """
        if request.expires_at is None:
            return False

        return datetime.now(timezone.utc) > request.expires_at

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        """获取待审核列表

        Returns:
            待审核请求列表
        """
        return [
            request for request in self.pending_approvals.values()
            if request.status == ApprovalStatus.PENDING
        ]