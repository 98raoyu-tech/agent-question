"""
工具生命周期仓储实现

提供工具评审、审批、安全扫描、使用分析和废弃实体的内存存储。
"""

import logging
from typing import Optional

from ...common.base_entity import BaseEntity
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.tool_approval import ToolApproval
from ..domain.tool_deprecation import ToolDeprecation
from ..domain.tool_review import ToolReview
from ..domain.tool_security_scan import ToolSecurityScan
from ..domain.tool_usage_analytics import ToolUsageAnalytics

logger = logging.getLogger(__name__)


class ToolLifecycleRepository:
    """工具生命周期仓储实现

    基于内存字典存储工具生命周期相关的所有实体。

    TODO: 后续替换为数据库实现
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._reviews: dict[str, ToolReview] = {}
        self._approvals: dict[str, ToolApproval] = {}
        self._security_scans: dict[str, ToolSecurityScan] = {}
        self._analytics: dict[str, ToolUsageAnalytics] = {}
        self._deprecations: dict[str, ToolDeprecation] = {}

    # ========== 评审操作 ==========

    async def save_review(self, review: ToolReview) -> ToolReview:
        """保存评审记录

        Args:
            review: 评审实体

        Returns:
            保存后的评审实体
        """
        self._reviews[review.id] = review
        return review

    async def find_review_by_id(self, review_id: str) -> Optional[ToolReview]:
        """根据ID查找评审

        Args:
            review_id: 评审标识

        Returns:
            评审实体，未找到返回None
        """
        review = self._reviews.get(review_id)
        if review is not None and review.is_deleted:
            return None
        return review

    async def find_reviews_by_tool(self, tool_id: str) -> list[ToolReview]:
        """查找工具的所有评审记录

        Args:
            tool_id: 工具标识

        Returns:
            评审列表
        """
        return [
            r for r in self._reviews.values()
            if r.tool_id == tool_id and not r.is_deleted
        ]

    # ========== 审批操作 ==========

    async def save_approval(self, approval: ToolApproval) -> ToolApproval:
        """保存审批记录

        Args:
            approval: 审批实体

        Returns:
            保存后的审批实体
        """
        self._approvals[approval.id] = approval
        return approval

    async def find_approval_by_id(self, approval_id: str) -> Optional[ToolApproval]:
        """根据ID查找审批

        Args:
            approval_id: 审批标识

        Returns:
            审批实体，未找到返回None
        """
        approval = self._approvals.get(approval_id)
        if approval is not None and approval.is_deleted:
            return None
        return approval

    async def find_approvals_by_tool(self, tool_id: str) -> list[ToolApproval]:
        """查找工具的所有审批记录

        Args:
            tool_id: 工具标识

        Returns:
            审批列表
        """
        return [
            a for a in self._approvals.values()
            if a.tool_id == tool_id and not a.is_deleted
        ]

    # ========== 安全扫描操作 ==========

    async def save_security_scan(self, scan: ToolSecurityScan) -> ToolSecurityScan:
        """保存安全扫描记录

        Args:
            scan: 安全扫描实体

        Returns:
            保存后的安全扫描实体
        """
        self._security_scans[scan.id] = scan
        return scan

    async def find_security_scan_by_id(self, scan_id: str) -> Optional[ToolSecurityScan]:
        """根据ID查找安全扫描

        Args:
            scan_id: 扫描标识

        Returns:
            安全扫描实体，未找到返回None
        """
        scan = self._security_scans.get(scan_id)
        if scan is not None and scan.is_deleted:
            return None
        return scan

    async def find_security_scans_by_tool(self, tool_id: str) -> list[ToolSecurityScan]:
        """查找工具的所有安全扫描记录

        Args:
            tool_id: 工具标识

        Returns:
            安全扫描列表
        """
        return [
            s for s in self._security_scans.values()
            if s.tool_id == tool_id and not s.is_deleted
        ]

    # ========== 使用分析操作 ==========

    async def save_analytics(self, analytics: ToolUsageAnalytics) -> ToolUsageAnalytics:
        """保存使用分析记录

        Args:
            analytics: 使用分析实体

        Returns:
            保存后的使用分析实体
        """
        self._analytics[analytics.id] = analytics
        return analytics

    async def find_analytics_by_tool(
        self,
        tool_id: str,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> list[ToolUsageAnalytics]:
        """查找工具的使用分析记录

        Args:
            tool_id: 工具标识
            period_start: 周期开始时间
            period_end: 周期结束时间

        Returns:
            使用分析列表
        """
        return [
            a for a in self._analytics.values()
            if a.tool_id == tool_id and not a.is_deleted
        ]

    # ========== 废弃操作 ==========

    async def save_deprecation(self, deprecation: ToolDeprecation) -> ToolDeprecation:
        """保存废弃记录

        Args:
            deprecation: 废弃实体

        Returns:
            保存后的废弃实体
        """
        self._deprecations[deprecation.id] = deprecation
        return deprecation

    async def find_deprecation_by_id(self, deprecation_id: str) -> Optional[ToolDeprecation]:
        """根据ID查找废弃记录

        Args:
            deprecation_id: 废弃标识

        Returns:
            废弃实体，未找到返回None
        """
        deprecation = self._deprecations.get(deprecation_id)
        if deprecation is not None and deprecation.is_deleted:
            return None
        return deprecation

    async def find_deprecations_by_tool(self, tool_id: str) -> list[ToolDeprecation]:
        """查找工具的所有废弃记录

        Args:
            tool_id: 工具标识

        Returns:
            废弃记录列表
        """
        return [
            d for d in self._deprecations.values()
            if d.tool_id == tool_id and not d.is_deleted
        ]
