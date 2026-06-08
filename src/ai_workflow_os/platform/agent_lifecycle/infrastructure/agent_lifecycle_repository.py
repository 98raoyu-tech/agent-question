"""
Agent Lifecycle仓储实现

提供Agent生命周期相关实体的内存存储实现，管理agents、versions、test_runs、
evaluations、approvals、deployments和rollbacks的独立字典存储。
"""

import logging
from typing import Optional

from ...common.base_repository import BaseRepository
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_approval import AgentApproval
from ..domain.agent_definition import AgentLifecycleDefinition
from ..domain.agent_deployment import AgentDeployment
from ..domain.agent_evaluation import AgentEvaluation
from ..domain.agent_rollback import AgentRollback
from ..domain.agent_test_run import AgentTestRun
from ..domain.agent_version import AgentLifecycleVersion

logger = logging.getLogger(__name__)


class AgentLifecycleRepository:
    """Agent生命周期仓储实现

    基于内存字典的仓储实现，为每种实体维护独立的存储字典。

    Attributes:
        _agents: Agent定义存储
        _versions: 版本存储
        _test_runs: 测试运行存储
        _evaluations: 评估存储
        _approvals: 审批存储
        _deployments: 部署存储
        _rollbacks: 回滚存储
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._agents: dict[str, AgentLifecycleDefinition] = {}
        self._versions: dict[str, AgentLifecycleVersion] = {}
        self._test_runs: dict[str, AgentTestRun] = {}
        self._evaluations: dict[str, AgentEvaluation] = {}
        self._approvals: dict[str, AgentApproval] = {}
        self._deployments: dict[str, AgentDeployment] = {}
        self._rollbacks: dict[str, AgentRollback] = {}

    def _find_in_store(
        self,
        store: dict,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ):
        """通用查找方法

        Args:
            store: 目标存储字典
            entity_id: 实体标识
            tenant_id: 租户标识

        Returns:
            实体实例，未找到返回None
        """
        entity = store.get(entity_id)
        if entity is not None and tenant_id is not None and entity.tenant_id != tenant_id:
            return None
        if entity is not None and entity.is_deleted:
            return None
        return entity

    def _find_all_in_store(
        self,
        store: dict,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse:
        """通用分页查询方法

        Args:
            store: 目标存储字典
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        items = [e for e in store.values() if not e.is_deleted]

        if tenant_id is not None:
            items = [e for e in items if e.tenant_id == tenant_id]

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if key == "search" and value:
                    search_term = value.lower()
                    items = [
                        e for e in items
                        if hasattr(e, "name") and search_term in getattr(e, "name", "").lower()
                    ]
                elif hasattr(items[0] if items else None, key):
                    items = [e for e in items if getattr(e, key, None) is not None]
                    enum_items = [e for e in items if getattr(e, key).value == value]
                    if enum_items:
                        items = enum_items
                    else:
                        items = [e for e in items if str(getattr(e, key)) == value]

        if pagination.sort_by and items and hasattr(items[0], pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            items.sort(key=lambda e: getattr(e, pagination.sort_by, ""), reverse=reverse)
        else:
            items.sort(key=lambda e: e.created_at, reverse=True)

        total = len(items)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = items[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def _save_to_store(self, store: dict, entity) -> None:
        """通用保存方法"""
        store[entity.id] = entity

    def _delete_from_store(
        self,
        store: dict,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """通用软删除方法"""
        entity = self._find_in_store(store, entity_id, tenant_id)
        if entity is None:
            return False
        entity.mark_deleted()
        return True

    def _count_in_store(
        self,
        store: dict,
        tenant_id: Optional[str] = None,
    ) -> int:
        """通用计数方法"""
        items = [e for e in store.values() if not e.is_deleted]
        if tenant_id is not None:
            items = [e for e in items if e.tenant_id == tenant_id]
        return len(items)

    # =========================================================================
    # Agent定义操作
    # =========================================================================

    async def find_agent_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentLifecycleDefinition]:
        return self._find_in_store(self._agents, entity_id, tenant_id)

    async def find_all_agents(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[AgentLifecycleDefinition]:
        return self._find_all_in_store(self._agents, pagination, tenant_id, filters)

    async def save_agent(self, entity: AgentLifecycleDefinition) -> AgentLifecycleDefinition:
        self._save_to_store(self._agents, entity)
        logger.debug("Agent已保存: id=%s", entity.id)
        return entity

    async def delete_agent(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        result = self._delete_from_store(self._agents, entity_id, tenant_id)
        if result:
            logger.debug("Agent已删除: id=%s", entity_id)
        return result

    async def agent_exists(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        return self._find_in_store(self._agents, entity_id, tenant_id) is not None

    async def count_agents(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> int:
        return self._count_in_store(self._agents, tenant_id)

    # =========================================================================
    # 版本操作
    # =========================================================================

    async def find_version_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentLifecycleVersion]:
        return self._find_in_store(self._versions, entity_id, tenant_id)

    async def find_all_versions(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[AgentLifecycleVersion]:
        return self._find_all_in_store(self._versions, pagination, tenant_id, filters)

    async def save_version(self, entity: AgentLifecycleVersion) -> AgentLifecycleVersion:
        self._save_to_store(self._versions, entity)
        logger.debug("Version已保存: id=%s", entity.id)
        return entity

    async def find_versions_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentLifecycleVersion]:
        return [
            v for v in self._versions.values()
            if v.agent_id == agent_id and not v.is_deleted
        ]

    # =========================================================================
    # 测试运行操作
    # =========================================================================

    async def find_test_run_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentTestRun]:
        return self._find_in_store(self._test_runs, entity_id, tenant_id)

    async def save_test_run(self, entity: AgentTestRun) -> AgentTestRun:
        self._save_to_store(self._test_runs, entity)
        logger.debug("TestRun已保存: id=%s", entity.id)
        return entity

    async def find_test_runs_by_version_id(
        self,
        version_id: str,
    ) -> list[AgentTestRun]:
        return [
            t for t in self._test_runs.values()
            if t.version_id == version_id and not t.is_deleted
        ]

    # =========================================================================
    # 评估操作
    # =========================================================================

    async def find_evaluation_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentEvaluation]:
        return self._find_in_store(self._evaluations, entity_id, tenant_id)

    async def save_evaluation(self, entity: AgentEvaluation) -> AgentEvaluation:
        self._save_to_store(self._evaluations, entity)
        logger.debug("Evaluation已保存: id=%s", entity.id)
        return entity

    async def find_evaluations_by_version_id(
        self,
        version_id: str,
    ) -> list[AgentEvaluation]:
        return [
            e for e in self._evaluations.values()
            if e.version_id == version_id and not e.is_deleted
        ]

    # =========================================================================
    # 审批操作
    # =========================================================================

    async def find_approval_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentApproval]:
        return self._find_in_store(self._approvals, entity_id, tenant_id)

    async def save_approval(self, entity: AgentApproval) -> AgentApproval:
        self._save_to_store(self._approvals, entity)
        logger.debug("Approval已保存: id=%s", entity.id)
        return entity

    async def find_approval_by_version_id(
        self,
        version_id: str,
    ) -> Optional[AgentApproval]:
        for approval in self._approvals.values():
            if approval.version_id == version_id and not approval.is_deleted:
                return approval
        return None

    # =========================================================================
    # 部署操作
    # =========================================================================

    async def find_deployment_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentDeployment]:
        return self._find_in_store(self._deployments, entity_id, tenant_id)

    async def find_all_deployments(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[AgentDeployment]:
        return self._find_all_in_store(self._deployments, pagination, tenant_id, filters)

    async def save_deployment(self, entity: AgentDeployment) -> AgentDeployment:
        self._save_to_store(self._deployments, entity)
        logger.debug("Deployment已保存: id=%s", entity.id)
        return entity

    async def find_deployments_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentDeployment]:
        return [
            d for d in self._deployments.values()
            if d.agent_id == agent_id and not d.is_deleted
        ]

    # =========================================================================
    # 回滚操作
    # =========================================================================

    async def find_rollback_by_id(
        self,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[AgentRollback]:
        return self._find_in_store(self._rollbacks, entity_id, tenant_id)

    async def save_rollback(self, entity: AgentRollback) -> AgentRollback:
        self._save_to_store(self._rollbacks, entity)
        logger.debug("Rollback已保存: id=%s", entity.id)
        return entity
