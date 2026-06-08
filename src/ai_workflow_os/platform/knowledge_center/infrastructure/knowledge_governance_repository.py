"""
知识治理仓储实现

提供知识治理相关实体的内存存储实现。
"""

import logging
from typing import Optional

from ..domain.knowledge_approval import KnowledgeApproval
from ..domain.knowledge_lineage import KnowledgeLineage
from ..domain.knowledge_publish_record import KnowledgePublishRecord
from ..domain.knowledge_review import KnowledgeReview
from ..domain.knowledge_version import KnowledgeVersion

logger = logging.getLogger(__name__)


class KnowledgeGovernanceRepository:
    """知识治理仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._versions: dict[str, KnowledgeVersion] = {}
        self._reviews: dict[str, KnowledgeReview] = {}
        self._approvals: dict[str, KnowledgeApproval] = {}
        self._lineage: dict[str, KnowledgeLineage] = {}
        self._publish_records: dict[str, KnowledgePublishRecord] = {}

    # =========================================================================
    # 版本操作
    # =========================================================================

    async def save_version(self, version: KnowledgeVersion) -> KnowledgeVersion:
        """保存版本

        Args:
            version: 版本实体

        Returns:
            保存后的版本实体
        """
        self._versions[version.id] = version
        return version

    async def find_version_by_id(self, version_id: str) -> Optional[KnowledgeVersion]:
        """根据ID查找版本

        Args:
            version_id: 版本标识

        Returns:
            版本实体，未找到返回None
        """
        version = self._versions.get(version_id)
        if version is not None and version.is_deleted:
            return None
        return version

    async def find_versions_by_source(self, source_id: str) -> list[KnowledgeVersion]:
        """查询知识源下的所有版本

        Args:
            source_id: 知识源标识

        Returns:
            版本列表
        """
        versions = [
            v for v in self._versions.values()
            if v.knowledge_source_id == source_id and not v.is_deleted
        ]
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions

    async def find_current_version(self, source_id: str) -> Optional[KnowledgeVersion]:
        """查询知识源的当前版本

        Args:
            source_id: 知识源标识

        Returns:
            当前版本实体，未找到返回None
        """
        for version in self._versions.values():
            if (
                version.knowledge_source_id == source_id
                and version.is_current
                and not version.is_deleted
            ):
                return version
        return None

    async def get_latest_version_number(self, source_id: str) -> int:
        """获取知识源的最新版本号

        Args:
            source_id: 知识源标识

        Returns:
            最新版本号，无版本时返回0
        """
        versions = await self.find_versions_by_source(source_id)
        if not versions:
            return 0
        return max(v.version_number for v in versions)

    # =========================================================================
    # 审核操作
    # =========================================================================

    async def save_review(self, review: KnowledgeReview) -> KnowledgeReview:
        """保存审核

        Args:
            review: 审核实体

        Returns:
            保存后的审核实体
        """
        self._reviews[review.id] = review
        return review

    async def find_review_by_id(self, review_id: str) -> Optional[KnowledgeReview]:
        """根据ID查找审核

        Args:
            review_id: 审核标识

        Returns:
            审核实体，未找到返回None
        """
        review = self._reviews.get(review_id)
        if review is not None and review.is_deleted:
            return None
        return review

    async def find_reviews_by_source(self, source_id: str) -> list[KnowledgeReview]:
        """查询知识源下的所有审核

        Args:
            source_id: 知识源标识

        Returns:
            审核列表
        """
        reviews = [
            r for r in self._reviews.values()
            if r.knowledge_source_id == source_id and not r.is_deleted
        ]
        reviews.sort(key=lambda r: r.created_at, reverse=True)
        return reviews

    async def find_reviews_by_version(self, version_id: str) -> list[KnowledgeReview]:
        """查询版本关联的所有审核

        Args:
            version_id: 版本标识

        Returns:
            审核列表
        """
        reviews = [
            r for r in self._reviews.values()
            if r.version_id == version_id and not r.is_deleted
        ]
        reviews.sort(key=lambda r: r.created_at, reverse=True)
        return reviews

    # =========================================================================
    # 审批操作
    # =========================================================================

    async def save_approval(self, approval: KnowledgeApproval) -> KnowledgeApproval:
        """保存审批

        Args:
            approval: 审批实体

        Returns:
            保存后的审批实体
        """
        self._approvals[approval.id] = approval
        return approval

    async def find_approval_by_id(self, approval_id: str) -> Optional[KnowledgeApproval]:
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

    async def find_approvals_by_source(self, source_id: str) -> list[KnowledgeApproval]:
        """查询知识源下的所有审批

        Args:
            source_id: 知识源标识

        Returns:
            审批列表
        """
        approvals = [
            a for a in self._approvals.values()
            if a.knowledge_source_id == source_id and not a.is_deleted
        ]
        approvals.sort(key=lambda a: a.created_at, reverse=True)
        return approvals

    # =========================================================================
    # 血缘操作
    # =========================================================================

    async def save_lineage(self, lineage: KnowledgeLineage) -> KnowledgeLineage:
        """保存血缘关系

        Args:
            lineage: 血缘实体

        Returns:
            保存后的血缘实体
        """
        self._lineage[lineage.id] = lineage
        return lineage

    async def find_lineage_by_source(self, source_id: str) -> list[KnowledgeLineage]:
        """查询知识源下的所有血缘关系

        Args:
            source_id: 知识源标识

        Returns:
            血缘关系列表
        """
        lineages = [
            l for l in self._lineage.values()
            if l.source_id == source_id and not l.is_deleted
        ]
        lineages.sort(key=lambda l: l.created_at, reverse=True)
        return lineages

    # =========================================================================
    # 发布记录操作
    # =========================================================================

    async def save_publish_record(
        self,
        record: KnowledgePublishRecord,
    ) -> KnowledgePublishRecord:
        """保存发布记录

        Args:
            record: 发布记录实体

        Returns:
            保存后的发布记录实体
        """
        self._publish_records[record.id] = record
        return record

    async def find_publish_record_by_id(
        self,
        record_id: str,
    ) -> Optional[KnowledgePublishRecord]:
        """根据ID查找发布记录

        Args:
            record_id: 发布记录标识

        Returns:
            发布记录实体，未找到返回None
        """
        record = self._publish_records.get(record_id)
        if record is not None and record.is_deleted:
            return None
        return record

    async def find_publish_history_by_source(
        self,
        source_id: str,
    ) -> list[KnowledgePublishRecord]:
        """查询知识源下的所有发布记录

        Args:
            source_id: 知识源标识

        Returns:
            发布记录列表
        """
        records = [
            r for r in self._publish_records.values()
            if r.knowledge_source_id == source_id and not r.is_deleted
        ]
        records.sort(key=lambda r: r.published_at, reverse=True)
        return records
