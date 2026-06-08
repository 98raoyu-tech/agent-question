"""
知识治理服务

提供知识版本、审核、审批、发布和血缘管理的完整生命周期业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ..domain.knowledge_approval import ApprovalStatus, KnowledgeApproval
from ..domain.knowledge_lineage import KnowledgeLineage
from ..domain.knowledge_publish_record import KnowledgePublishRecord, PublishStatus
from ..domain.knowledge_review import KnowledgeReview, ReviewStatus
from ..domain.knowledge_version import KnowledgeVersion, VersionStatus
from ..infrastructure.knowledge_governance_repository import KnowledgeGovernanceRepository

logger = logging.getLogger(__name__)


class KnowledgeGovernanceService:
    """知识治理业务服务

    提供知识版本管理、审核流程、审批流程、发布管理和血缘追踪。

    Attributes:
        repository: 知识治理仓储实例
    """

    def __init__(self, repository: KnowledgeGovernanceRepository) -> None:
        """初始化知识治理服务

        Args:
            repository: 知识治理仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 版本管理
    # =========================================================================

    async def create_version(
        self,
        source_id: str,
        change_log: str = "",
        snapshot: Optional[dict] = None,
        operator: Optional[str] = None,
    ) -> KnowledgeVersion:
        """创建知识版本

        基于知识源创建新的版本记录，版本号自动递增。

        Args:
            source_id: 知识源标识
            change_log: 变更日志
            snapshot: 版本快照数据
            operator: 操作者标识

        Returns:
            创建后的版本实体

        Raises:
            ValidationException: 知识源标识为空
        """
        if not source_id:
            raise ValidationException(message="知识源标识不能为空")

        latest_number = await self.repository.get_latest_version_number(source_id)
        version = KnowledgeVersion(
            knowledge_source_id=source_id,
            version_number=latest_number + 1,
            change_log=change_log,
            snapshot=snapshot or {},
        )
        version.created_by = operator
        version.updated_by = operator

        saved_version = await self.repository.save_version(version)
        logger.info(
            "知识版本创建成功: id=%s, source_id=%s, version_number=%d",
            saved_version.id,
            source_id,
            saved_version.version_number,
        )

        return saved_version

    async def get_versions(self, source_id: str) -> list[KnowledgeVersion]:
        """获取知识源的所有版本

        Args:
            source_id: 知识源标识

        Returns:
            版本列表
        """
        return await self.repository.find_versions_by_source(source_id)

    # =========================================================================
    # 审核流程
    # =========================================================================

    async def submit_review(
        self,
        version_id: str,
        reviewer_id: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeReview:
        """提交审核

        为指定版本创建审核记录，版本状态变为审核中。

        Args:
            version_id: 版本标识
            reviewer_id: 审核人标识
            operator: 操作者标识

        Returns:
            创建后的审核实体

        Raises:
            ResourceNotFoundException: 版本不存在
            BusinessRuleViolationException: 版本状态不允许提交审核
        """
        version = await self._get_version_or_raise(version_id)

        if version.status not in (VersionStatus.DRAFT, VersionStatus.APPROVED):
            raise BusinessRuleViolationException(
                rule="REVIEW_SUBMIT_TRANSITION",
                message=f"版本状态 [{version.status.value}] 不允许提交审核",
            )

        version.status = VersionStatus.REVIEW
        await self.repository.save_version(version)

        review = KnowledgeReview(
            knowledge_source_id=version.knowledge_source_id,
            version_id=version_id,
            reviewer_id=reviewer_id,
        )
        review.created_by = operator
        review.updated_by = operator

        saved_review = await self.repository.save_review(review)
        logger.info(
            "审核提交成功: id=%s, version_id=%s",
            saved_review.id,
            version_id,
        )

        return saved_review

    async def approve_review(
        self,
        review_id: str,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeReview:
        """通过审核

        Args:
            review_id: 审核标识
            reviewer: 审核人标识
            notes: 审核意见
            operator: 操作者标识

        Returns:
            更新后的审核实体

        Raises:
            ResourceNotFoundException: 审核不存在
        """
        review = await self._get_review_or_raise(review_id)
        review.approve(reviewer, notes, operator)

        await self.repository.save_review(review)
        logger.info("审核通过: id=%s, reviewer=%s", review_id, reviewer)

        return review

    async def reject_review(
        self,
        review_id: str,
        reviewer: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeReview:
        """驳回审核

        Args:
            review_id: 审核标识
            reviewer: 审核人标识
            reason: 驳回原因
            operator: 操作者标识

        Returns:
            更新后的审核实体

        Raises:
            ResourceNotFoundException: 审核不存在
        """
        review = await self._get_review_or_raise(review_id)
        review.reject(reviewer, reason, operator)

        await self.repository.save_review(review)
        logger.info("审核驳回: id=%s, reviewer=%s", review_id, reviewer)

        return review

    async def get_reviews(self, source_id: str) -> list[KnowledgeReview]:
        """获取知识源的所有审核记录

        Args:
            source_id: 知识源标识

        Returns:
            审核列表
        """
        return await self.repository.find_reviews_by_source(source_id)

    # =========================================================================
    # 审批流程
    # =========================================================================

    async def submit_approval(
        self,
        version_id: str,
        requester: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeApproval:
        """提交审批

        为已通过审核的版本创建审批记录。

        Args:
            version_id: 版本标识
            requester: 发起人标识
            operator: 操作者标识

        Returns:
            创建后的审批实体

        Raises:
            ResourceNotFoundException: 版本不存在
            BusinessRuleViolationException: 版本状态不允许提交审批
        """
        version = await self._get_version_or_raise(version_id)

        if version.status != VersionStatus.REVIEW:
            raise BusinessRuleViolationException(
                rule="APPROVAL_SUBMIT_TRANSITION",
                message=f"版本状态 [{version.status.value}] 不允许提交审批，仅 REVIEW 状态可提交",
            )

        # 检查是否有已通过的审核
        reviews = await self.repository.find_reviews_by_version(version_id)
        has_approved = any(r.status == ReviewStatus.APPROVED for r in reviews)
        if not has_approved:
            raise BusinessRuleViolationException(
                rule="APPROVAL_REVIEW_REQUIRED",
                message="版本需要至少一个已通过的审核才能提交审批",
            )

        approval = KnowledgeApproval(
            knowledge_source_id=version.knowledge_source_id,
            version_id=version_id,
            requested_by=requester,
        )
        approval.created_by = operator
        approval.updated_by = operator

        saved_approval = await self.repository.save_approval(approval)
        logger.info(
            "审批提交成功: id=%s, version_id=%s",
            saved_approval.id,
            version_id,
        )

        return saved_approval

    async def approve_version(
        self,
        approval_id: str,
        approver: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeApproval:
        """批准版本审批

        Args:
            approval_id: 审批标识
            approver: 审批人标识
            notes: 审批意见
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self._get_approval_or_raise(approval_id)
        approval.approve(approver, notes, operator)

        # 更新关联版本状态为已批准
        version = await self._get_version_or_raise(approval.version_id)
        version.status = VersionStatus.APPROVED
        await self.repository.save_version(version)
        await self.repository.save_approval(approval)

        logger.info("审批通过: id=%s, approver=%s", approval_id, approver)

        return approval

    async def reject_approval(
        self,
        approval_id: str,
        approver: str,
        reason: str = "",
        operator: Optional[str] = None,
    ) -> KnowledgeApproval:
        """驳回版本审批

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

        await self.repository.save_approval(approval)
        logger.info("审批驳回: id=%s, approver=%s", approval_id, approver)

        return approval

    # =========================================================================
    # 发布管理
    # =========================================================================

    async def publish_version(
        self,
        version_id: str,
        environment: str = "production",
        operator: Optional[str] = None,
    ) -> KnowledgePublishRecord:
        """发布版本

        发布已批准的版本，并创建发布记录。如果存在当前版本，取消其当前标记。

        Args:
            version_id: 版本标识
            environment: 发布环境
            operator: 操作者标识

        Returns:
            发布记录实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self._get_version_or_raise(version_id)
        version.publish(operator)

        # 取消当前源下其他版本的当前标记
        current_version = await self.repository.find_current_version(
            version.knowledge_source_id,
        )
        if current_version is not None and current_version.id != version_id:
            current_version.is_current = False
            await self.repository.save_version(current_version)

        await self.repository.save_version(version)

        record = KnowledgePublishRecord(
            knowledge_source_id=version.knowledge_source_id,
            version_id=version_id,
            published_by=operator or "",
            environment=environment,
        )
        record.created_by = operator
        record.updated_by = operator

        saved_record = await self.repository.save_publish_record(record)
        logger.info(
            "版本发布成功: version_id=%s, environment=%s",
            version_id,
            environment,
        )

        return saved_record

    async def rollback_publish(
        self,
        publish_id: str,
        target_version_id: str,
        operator: Optional[str] = None,
    ) -> KnowledgePublishRecord:
        """回滚发布

        将已发布的版本回滚到指定目标版本。

        Args:
            publish_id: 发布记录标识
            target_version_id: 回滚目标版本标识
            operator: 操作者标识

        Returns:
            更新后的发布记录实体

        Raises:
            ResourceNotFoundException: 发布记录或目标版本不存在
        """
        record = await self._get_publish_record_or_raise(publish_id)
        record.rollback(target_version_id, operator)

        # 将目标版本设为当前版本
        target_version = await self._get_version_or_raise(target_version_id)
        target_version.is_current = True
        await self.repository.save_version(target_version)

        await self.repository.save_publish_record(record)
        logger.info(
            "发布回滚成功: publish_id=%s, target_version_id=%s",
            publish_id,
            target_version_id,
        )

        return record

    async def get_publish_history(
        self,
        source_id: str,
    ) -> list[KnowledgePublishRecord]:
        """获取知识源的发布历史

        Args:
            source_id: 知识源标识

        Returns:
            发布记录列表
        """
        return await self.repository.find_publish_history_by_source(source_id)

    # =========================================================================
    # 血缘追踪
    # =========================================================================

    async def get_lineage(self, source_id: str) -> list[KnowledgeLineage]:
        """获取知识源的血缘关系

        Args:
            source_id: 知识源标识

        Returns:
            血缘关系列表
        """
        return await self.repository.find_lineage_by_source(source_id)

    async def create_lineage(
        self,
        source_id: str,
        parent_version_id: str,
        child_version_id: str,
        transformation_type: str = "",
        transformation_details: Optional[dict] = None,
        operator: Optional[str] = None,
    ) -> KnowledgeLineage:
        """创建血缘关系

        Args:
            source_id: 知识源标识
            parent_version_id: 父版本标识
            child_version_id: 子版本标识
            transformation_type: 转换类型
            transformation_details: 转换详情
            operator: 操作者标识

        Returns:
            创建后的血缘实体
        """
        lineage = KnowledgeLineage.link(
            parent_id=parent_version_id,
            child_id=child_version_id,
            source_id=source_id,
            transformation_type=transformation_type,
            transformation_details=transformation_details,
            operator=operator,
        )

        saved_lineage = await self.repository.save_lineage(lineage)
        logger.info(
            "血缘关系创建成功: parent=%s -> child=%s",
            parent_version_id,
            child_version_id,
        )

        return saved_lineage

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _get_version_or_raise(self, version_id: str) -> KnowledgeVersion:
        """获取版本实体，不存在则抛出异常

        Args:
            version_id: 版本标识

        Returns:
            版本实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self.repository.find_version_by_id(version_id)
        if version is None:
            raise ResourceNotFoundException(resource_type="版本", resource_id=version_id)
        return version

    async def _get_review_or_raise(self, review_id: str) -> KnowledgeReview:
        """获取审核实体，不存在则抛出异常

        Args:
            review_id: 审核标识

        Returns:
            审核实体

        Raises:
            ResourceNotFoundException: 审核不存在
        """
        review = await self.repository.find_review_by_id(review_id)
        if review is None:
            raise ResourceNotFoundException(resource_type="审核", resource_id=review_id)
        return review

    async def _get_approval_or_raise(self, approval_id: str) -> KnowledgeApproval:
        """获取审批实体，不存在则抛出异常

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

    async def _get_publish_record_or_raise(
        self,
        record_id: str,
    ) -> KnowledgePublishRecord:
        """获取发布记录实体，不存在则抛出异常

        Args:
            record_id: 发布记录标识

        Returns:
            发布记录实体

        Raises:
            ResourceNotFoundException: 发布记录不存在
        """
        record = await self.repository.find_publish_record_by_id(record_id)
        if record is None:
            raise ResourceNotFoundException(resource_type="发布记录", resource_id=record_id)
        return record
