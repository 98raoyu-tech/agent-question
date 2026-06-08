"""
Agent Pipeline 仓储实现

提供流水线和步骤实体的内存存储实现。
"""

import logging

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.pipeline import AgentPipeline
from ..domain.pipeline_step import PipelineStep

logger = logging.getLogger(__name__)


class AgentPipelineRepository:
    """Agent Pipeline 仓储实现

    基于内存字典的仓储实现，管理流水线和步骤的持久化。

    Attributes:
        _pipelines: 流水线存储
        _steps: 步骤存储
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._pipelines: dict[str, AgentPipeline] = {}
        self._steps: dict[str, PipelineStep] = {}

    # =========================================================================
    # 流水线操作
    # =========================================================================

    async def find_pipeline_by_id(
        self,
        entity_id: str,
        tenant_id: str | None = None,
    ) -> AgentPipeline | None:
        """根据ID查找流水线

        Args:
            entity_id: 流水线标识
            tenant_id: 租户标识

        Returns:
            流水线实体，未找到返回None
        """
        pipeline = self._pipelines.get(entity_id)
        if pipeline is not None and tenant_id is not None and pipeline.tenant_id != tenant_id:
            return None
        if pipeline is not None and pipeline.is_deleted:
            return None
        return pipeline

    async def find_pipelines_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentPipeline]:
        """根据Agent标识查找流水线列表

        Args:
            agent_id: Agent标识

        Returns:
            流水线列表
        """
        return [
            p for p in self._pipelines.values()
            if p.agent_id == agent_id and not p.is_deleted
        ]

    async def find_latest_pipeline(
        self,
        agent_id: str,
        version_id: str | None = None,
    ) -> AgentPipeline | None:
        """查找最新的流水线

        Args:
            agent_id: Agent标识
            version_id: 版本标识（可选）

        Returns:
            最新的流水线，未找到返回None
        """
        pipelines = [
            p for p in self._pipelines.values()
            if p.agent_id == agent_id and not p.is_deleted
        ]
        if version_id:
            pipelines = [p for p in pipelines if p.version_id == version_id]

        if not pipelines:
            return None

        pipelines.sort(key=lambda p: p.created_at, reverse=True)
        return pipelines[0]

    async def find_all_pipelines(
        self,
        pagination: PaginatedRequest,
        tenant_id: str | None = None,
        filters: dict | None = None,
    ) -> PaginatedResponse[AgentPipeline]:
        """分页查询流水线列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        items = [p for p in self._pipelines.values() if not p.is_deleted]

        if tenant_id is not None:
            items = [p for p in items if p.tenant_id == tenant_id]

        if filters:
            if filters.get("agent_id"):
                items = [p for p in items if p.agent_id == filters["agent_id"]]
            if filters.get("status"):
                items = [p for p in items if p.status.value == filters["status"]]

        items.sort(key=lambda p: p.created_at, reverse=True)
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

    async def save_pipeline(self, entity: AgentPipeline) -> AgentPipeline:
        """保存流水线

        Args:
            entity: 流水线实体

        Returns:
            保存后的流水线
        """
        self._pipelines[entity.id] = entity
        logger.debug("Pipeline已保存: id=%s", entity.id)
        return entity

    # =========================================================================
    # 步骤操作
    # =========================================================================

    async def find_step_by_id(
        self,
        entity_id: str,
        tenant_id: str | None = None,
    ) -> PipelineStep | None:
        """根据ID查找步骤

        Args:
            entity_id: 步骤标识
            tenant_id: 租户标识

        Returns:
            步骤实体，未找到返回None
        """
        step = self._steps.get(entity_id)
        if step is not None and tenant_id is not None and step.tenant_id != tenant_id:
            return None
        if step is not None and step.is_deleted:
            return None
        return step

    async def find_steps_by_pipeline_id(
        self,
        pipeline_id: str,
    ) -> list[PipelineStep]:
        """根据流水线标识查找步骤列表

        Args:
            pipeline_id: 流水线标识

        Returns:
            步骤列表
        """
        return [
            s for s in self._steps.values()
            if s.pipeline_id == pipeline_id and not s.is_deleted
        ]

    async def save_step(self, entity: PipelineStep) -> PipelineStep:
        """保存步骤

        Args:
            entity: 步骤实体

        Returns:
            保存后的步骤
        """
        self._steps[entity.id] = entity
        logger.debug("PipelineStep已保存: id=%s, stage=%s", entity.id, entity.stage.value)
        return entity

    async def save_steps(self, entities: list[PipelineStep]) -> list[PipelineStep]:
        """批量保存步骤

        Args:
            entities: 步骤实体列表

        Returns:
            保存后的步骤列表
        """
        for entity in entities:
            self._steps[entity.id] = entity
        logger.debug("批量保存PipelineStep: count=%d", len(entities))
        return entities
