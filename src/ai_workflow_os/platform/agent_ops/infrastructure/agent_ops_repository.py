"""
Agent Ops 仓储实现

提供Agent运维管理实体的内存存储实现，后续替换为数据库持久化。
"""

import logging
from typing import Any, Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.deployment import Deployment
from ..domain.incident import Incident
from ..domain.runbook import Runbook
from ..domain.sla import SLA
from ..domain.slo import SLO

logger = logging.getLogger(__name__)


class AgentOpsRepository:
    """Agent Ops 仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._deployments: dict[str, Deployment] = {}
        self._incidents: dict[str, Incident] = {}
        self._runbooks: dict[str, Runbook] = {}
        self._slas: dict[str, SLA] = {}
        self._slos: dict[str, SLO] = {}

    # =============================================================================
    # 部署仓储
    # =============================================================================

    async def find_deployment_by_id(self, entity_id: str) -> Optional[Deployment]:
        """根据ID查找部署

        Args:
            entity_id: 部署标识

        Returns:
            部署实体，未找到返回None
        """
        deployment = self._deployments.get(entity_id)
        if deployment is not None and deployment.is_deleted:
            return None
        return deployment

    async def find_all_deployments(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse[Deployment]:
        """分页查询部署列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        deployments = [d for d in self._deployments.values() if not d.is_deleted]
        deployments = self._apply_deployment_filters(deployments, filters)
        deployments = self._apply_sorting(deployments, pagination)

        total = len(deployments)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = deployments[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_deployment(self, entity: Deployment) -> Deployment:
        """保存部署

        Args:
            entity: 部署实体

        Returns:
            保存后的部署实体
        """
        self._deployments[entity.id] = entity
        logger.debug("部署已保存: id=%s", entity.id)
        return entity

    # =============================================================================
    # 事故仓储
    # =============================================================================

    async def find_incident_by_id(self, entity_id: str) -> Optional[Incident]:
        """根据ID查找事故

        Args:
            entity_id: 事故标识

        Returns:
            事故实体，未找到返回None
        """
        incident = self._incidents.get(entity_id)
        if incident is not None and incident.is_deleted:
            return None
        return incident

    async def find_all_incidents(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse[Incident]:
        """分页查询事故列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        incidents = [i for i in self._incidents.values() if not i.is_deleted]
        incidents = self._apply_incident_filters(incidents, filters)
        incidents = self._apply_sorting(incidents, pagination)

        total = len(incidents)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = incidents[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_incident(self, entity: Incident) -> Incident:
        """保存事故

        Args:
            entity: 事故实体

        Returns:
            保存后的事故实体
        """
        self._incidents[entity.id] = entity
        logger.debug("事故已保存: id=%s", entity.id)
        return entity

    # =============================================================================
    # 运维手册仓储
    # =============================================================================

    async def find_runbook_by_id(self, entity_id: str) -> Optional[Runbook]:
        """根据ID查找运维手册

        Args:
            entity_id: 运维手册标识

        Returns:
            运维手册实体，未找到返回None
        """
        runbook = self._runbooks.get(entity_id)
        if runbook is not None and runbook.is_deleted:
            return None
        return runbook

    async def find_all_runbooks(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse[Runbook]:
        """分页查询运维手册列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        runbooks = [r for r in self._runbooks.values() if not r.is_deleted]
        runbooks = self._apply_runbook_filters(runbooks, filters)
        runbooks = self._apply_sorting(runbooks, pagination)

        total = len(runbooks)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = runbooks[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_runbook(self, entity: Runbook) -> Runbook:
        """保存运维手册

        Args:
            entity: 运维手册实体

        Returns:
            保存后的运维手册实体
        """
        self._runbooks[entity.id] = entity
        logger.debug("运维手册已保存: id=%s", entity.id)
        return entity

    # =============================================================================
    # SLA仓储
    # =============================================================================

    async def find_sla_by_id(self, entity_id: str) -> Optional[SLA]:
        """根据ID查找SLA

        Args:
            entity_id: SLA标识

        Returns:
            SLA实体，未找到返回None
        """
        sla = self._slas.get(entity_id)
        if sla is not None and sla.is_deleted:
            return None
        return sla

    async def find_all_slas(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse[SLA]:
        """分页查询SLA列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        slas = [s for s in self._slas.values() if not s.is_deleted]
        slas = self._apply_sla_filters(slas, filters)
        slas = self._apply_sorting(slas, pagination)

        total = len(slas)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = slas[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_sla(self, entity: SLA) -> SLA:
        """保存SLA

        Args:
            entity: SLA实体

        Returns:
            保存后的SLA实体
        """
        self._slas[entity.id] = entity
        logger.debug("SLA已保存: id=%s", entity.id)
        return entity

    # =============================================================================
    # SLO仓储
    # =============================================================================

    async def find_slo_by_id(self, entity_id: str) -> Optional[SLO]:
        """根据ID查找SLO

        Args:
            entity_id: SLO标识

        Returns:
            SLO实体，未找到返回None
        """
        slo = self._slos.get(entity_id)
        if slo is not None and slo.is_deleted:
            return None
        return slo

    async def find_all_slos(
        self,
        pagination: PaginatedRequest,
        filters: Optional[dict[str, Any]] = None,
    ) -> PaginatedResponse[SLO]:
        """分页查询SLO列表

        Args:
            pagination: 分页参数
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        slos = [s for s in self._slos.values() if not s.is_deleted]
        slos = self._apply_slo_filters(slos, filters)
        slos = self._apply_sorting(slos, pagination)

        total = len(slos)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = slos[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_slo(self, entity: SLO) -> SLO:
        """保存SLO

        Args:
            entity: SLO实体

        Returns:
            保存后的SLO实体
        """
        self._slos[entity.id] = entity
        logger.debug("SLO已保存: id=%s", entity.id)
        return entity

    # =============================================================================
    # 过滤辅助方法
    # =============================================================================

    def _apply_deployment_filters(
        self,
        deployments: list[Deployment],
        filters: Optional[dict[str, Any]],
    ) -> list[Deployment]:
        """应用部署过滤条件"""
        if not filters:
            return deployments

        filtered = deployments
        if "agent_id" in filters:
            filtered = [d for d in filtered if d.agent_id == filters["agent_id"]]
        if "environment" in filters:
            filtered = [d for d in filtered if d.environment.value == filters["environment"]]
        if "status" in filters:
            filtered = [d for d in filtered if d.status.value == filters["status"]]

        return filtered

    def _apply_incident_filters(
        self,
        incidents: list[Incident],
        filters: Optional[dict[str, Any]],
    ) -> list[Incident]:
        """应用事故过滤条件"""
        if not filters:
            return incidents

        filtered = incidents
        if "agent_id" in filters:
            filtered = [i for i in filtered if i.agent_id == filters["agent_id"]]
        if "severity" in filters:
            filtered = [i for i in filtered if i.severity.value == filters["severity"]]
        if "status" in filters:
            filtered = [i for i in filtered if i.status.value == filters["status"]]

        return filtered

    def _apply_runbook_filters(
        self,
        runbooks: list[Runbook],
        filters: Optional[dict[str, Any]],
    ) -> list[Runbook]:
        """应用运维手册过滤条件"""
        if not filters:
            return runbooks

        filtered = runbooks
        if "agent_id" in filters:
            filtered = [r for r in filtered if r.agent_id == filters["agent_id"]]
        if "is_active" in filters:
            filtered = [r for r in filtered if r.is_active == filters["is_active"]]

        return filtered

    def _apply_sla_filters(
        self,
        slas: list[SLA],
        filters: Optional[dict[str, Any]],
    ) -> list[SLA]:
        """应用SLA过滤条件"""
        if not filters:
            return slas

        filtered = slas
        if "agent_id" in filters:
            filtered = [s for s in filtered if s.agent_id == filters["agent_id"]]

        return filtered

    def _apply_slo_filters(
        self,
        slos: list[SLO],
        filters: Optional[dict[str, Any]],
    ) -> list[SLO]:
        """应用SLO过滤条件"""
        if not filters:
            return slos

        filtered = slos
        if "agent_id" in filters:
            filtered = [s for s in filtered if s.agent_id == filters["agent_id"]]
        if "sla_id" in filters:
            filtered = [s for s in filtered if s.sla_id == filters["sla_id"]]

        return filtered

    def _apply_sorting(
        self,
        items: list[Any],
        pagination: PaginatedRequest,
    ) -> list[Any]:
        """应用排序"""
        if pagination.sort_by and items and hasattr(items[0], pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            items.sort(key=lambda x: getattr(x, pagination.sort_by, ""), reverse=reverse)
        else:
            items.sort(key=lambda x: x.created_at, reverse=True)

        return items
