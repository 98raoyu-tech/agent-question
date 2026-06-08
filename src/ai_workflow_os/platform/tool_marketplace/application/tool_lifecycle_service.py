"""
工具生命周期服务

编排工具评审、审批、安全扫描、使用分析和废弃的业务流程。
"""

import logging
from datetime import datetime
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ..domain.tool_approval import ApprovalStatus, ToolApproval
from ..domain.tool_deprecation import DeprecationStatus, ToolDeprecation
from ..domain.tool_review import ReviewStatus, ToolReview
from ..domain.tool_security_scan import ScanType, ToolSecurityScan
from ..domain.tool_usage_analytics import ToolUsageAnalytics
from ..infrastructure.tool_lifecycle_repository import ToolLifecycleRepository

logger = logging.getLogger(__name__)


class ToolLifecycleService:
    """工具生命周期业务服务

    提供工具评审、审批、安全扫描、使用分析和废弃的完整管理能力。

    Attributes:
        repository: 生命周期仓储实例
    """

    def __init__(self, repository: ToolLifecycleRepository) -> None:
        """初始化生命周期服务

        Args:
            repository: 生命周期仓储实例
        """
        self.repository = repository

    # ========== 评审流程 ==========

    async def submit_review(
        self,
        tool_id: str,
        operator: Optional[str] = None,
    ) -> ToolReview:
        """提交工具评审

        Args:
            tool_id: 工具标识
            operator: 操作者标识

        Returns:
            创建的评审实体
        """
        if not tool_id:
            raise ValidationException(message="工具标识不能为空")

        review = ToolReview(
            tool_id=tool_id,
            created_by=operator,
            updated_by=operator,
        )
        saved = await self.repository.save_review(review)
        logger.info("评审提交成功: tool_id=%s, review_id=%s", tool_id, saved.id)
        return saved

    async def approve_review(
        self,
        review_id: str,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> ToolReview:
        """通过评审

        Args:
            review_id: 评审标识
            reviewer: 评审人标识
            notes: 评审备注
            operator: 操作者标识

        Returns:
            更新后的评审实体

        Raises:
            ResourceNotFoundException: 评审不存在
        """
        review = await self._get_review_or_raise(review_id)
        review.approve(reviewer, notes, operator)
        saved = await self.repository.save_review(review)
        logger.info("评审通过: review_id=%s, reviewer=%s", review_id, reviewer)
        return saved

    async def reject_review(
        self,
        review_id: str,
        reviewer: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> ToolReview:
        """驳回评审

        Args:
            review_id: 评审标识
            reviewer: 评审人标识
            reason: 驳回原因
            operator: 操作者标识

        Returns:
            更新后的评审实体

        Raises:
            ResourceNotFoundException: 评审不存在
        """
        review = await self._get_review_or_raise(review_id)
        review.reject(reviewer, reason, operator)
        saved = await self.repository.save_review(review)
        logger.info("评审驳回: review_id=%s, reviewer=%s", review_id, reviewer)
        return saved

    async def get_reviews(self, tool_id: str) -> list[ToolReview]:
        """获取工具的评审列表

        Args:
            tool_id: 工具标识

        Returns:
            评审列表
        """
        return await self.repository.find_reviews_by_tool(tool_id)

    # ========== 审批流程 ==========

    async def submit_approval(
        self,
        tool_id: str,
        version_id: str,
        operator: Optional[str] = None,
    ) -> ToolApproval:
        """提交工具审批

        Args:
            tool_id: 工具标识
            version_id: 版本标识
            operator: 操作者标识

        Returns:
            创建的审批实体
        """
        if not tool_id or not version_id:
            raise ValidationException(message="工具标识和版本标识不能为空")

        approval = ToolApproval(
            tool_id=tool_id,
            version_id=version_id,
            requested_by=operator or "",
            requested_at=datetime.utcnow(),
            created_by=operator,
            updated_by=operator,
        )
        saved = await self.repository.save_approval(approval)
        logger.info(
            "审批提交成功: tool_id=%s, version_id=%s, approval_id=%s",
            tool_id, version_id, saved.id,
        )
        return saved

    async def approve_tool(
        self,
        approval_id: str,
        approver: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> ToolApproval:
        """批准工具

        Args:
            approval_id: 审批标识
            approver: 审批人标识
            notes: 审批备注
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self._get_approval_or_raise(approval_id)
        approval.approve(approver, notes, operator)
        saved = await self.repository.save_approval(approval)
        logger.info("工具审批通过: approval_id=%s, approver=%s", approval_id, approver)
        return saved

    async def reject_approval(
        self,
        approval_id: str,
        approver: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> ToolApproval:
        """驳回工具

        Args:
            approval_id: 审批标识
            approver: 审批人标识
            reason: 驳回原因
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self._get_approval_or_raise(approval_id)
        approval.reject(approver, reason, operator)
        saved = await self.repository.save_approval(approval)
        logger.info("工具审批驳回: approval_id=%s, approver=%s", approval_id, approver)
        return saved

    async def get_approval_history(self, tool_id: str) -> list[ToolApproval]:
        """获取工具的审批历史

        Args:
            tool_id: 工具标识

        Returns:
            审批列表
        """
        return await self.repository.find_approvals_by_tool(tool_id)

    # ========== 安全扫描流程 ==========

    async def run_security_scan(
        self,
        tool_id: str,
        version_id: str,
        scan_type: ScanType,
        operator: Optional[str] = None,
    ) -> ToolSecurityScan:
        """启动安全扫描

        Args:
            tool_id: 工具标识
            version_id: 版本标识
            scan_type: 扫描类型
            operator: 操作者标识

        Returns:
            创建的安全扫描实体
        """
        if not tool_id or not version_id:
            raise ValidationException(message="工具标识和版本标识不能为空")

        scan = ToolSecurityScan(
            tool_id=tool_id,
            version_id=version_id,
            scan_type=scan_type,
            created_by=operator,
            updated_by=operator,
        )
        scan.start_scan(operator)
        saved = await self.repository.save_security_scan(scan)
        logger.info(
            "安全扫描启动: tool_id=%s, version_id=%s, scan_type=%s, scan_id=%s",
            tool_id, version_id, scan_type.value, saved.id,
        )
        return saved

    async def get_security_scans(self, tool_id: str) -> list[ToolSecurityScan]:
        """获取工具的安全扫描记录

        Args:
            tool_id: 工具标识

        Returns:
            安全扫描列表
        """
        return await self.repository.find_security_scans_by_tool(tool_id)

    # ========== 使用分析 ==========

    async def get_usage_analytics(
        self,
        tool_id: str,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> list[ToolUsageAnalytics]:
        """获取工具使用分析

        Args:
            tool_id: 工具标识
            period_start: 周期开始时间
            period_end: 周期结束时间

        Returns:
            使用分析列表
        """
        return await self.repository.find_analytics_by_tool(
            tool_id, period_start, period_end,
        )

    # ========== 废弃流程 ==========

    async def deprecate_tool(
        self,
        tool_id: str,
        reason: str,
        sunset_date: Optional[datetime] = None,
        operator: Optional[str] = None,
        replacement_tool_id: Optional[str] = None,
        migration_guide: str = "",
    ) -> ToolDeprecation:
        """废弃工具

        Args:
            tool_id: 工具标识
            reason: 废弃原因
            sunset_date: 计划下线日期
            operator: 操作者标识
            replacement_tool_id: 替代工具标识
            migration_guide: 迁移指引

        Returns:
            创建的废弃实体
        """
        if not tool_id:
            raise ValidationException(message="工具标识不能为空")
        if not reason:
            raise ValidationException(message="废弃原因不能为空")

        deprecation = ToolDeprecation(
            tool_id=tool_id,
            reason=reason,
            deprecated_by=operator or "",
            sunset_date=sunset_date,
            replacement_tool_id=replacement_tool_id,
            migration_guide=migration_guide,
            created_by=operator,
            updated_by=operator,
        )
        deprecation.announce(operator)
        saved = await self.repository.save_deprecation(deprecation)
        logger.info("工具废弃公告发布: tool_id=%s, deprecation_id=%s", tool_id, saved.id)
        return saved

    # ========== 内部方法 ==========

    async def _get_review_or_raise(self, review_id: str) -> ToolReview:
        """获取评审或抛出异常

        Args:
            review_id: 评审标识

        Returns:
            评审实体

        Raises:
            ResourceNotFoundException: 评审不存在
        """
        review = await self.repository.find_review_by_id(review_id)
        if review is None:
            raise ResourceNotFoundException(resource_type="评审", resource_id=review_id)
        return review

    async def _get_approval_or_raise(self, approval_id: str) -> ToolApproval:
        """获取审批或抛出异常

        Args:
            approval_id: 审批标识

        Returns:
            审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self.repository.find_approval_by_id(approval_id)
        if approval is None:
            raise ResourceNotFoundException(resource_type="审批", resource_id=approval_id)
        return approval
