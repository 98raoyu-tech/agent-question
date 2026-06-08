"""
Agent Pipeline 服务

提供Agent发布流水线的完整业务逻辑，包括流水线创建、启动、
阶段推进、评估门禁检查、审批、发布、部署和回滚。
"""

import logging

from ....core.events import EventBus
from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import (
    PipelineStage,
    PipelineStatus,
)
from ..domain.pipeline import AgentPipeline
from ..infrastructure.pipeline_repository import AgentPipelineRepository

logger = logging.getLogger(__name__)


class AgentPipelineService:
    """Agent发布流水线业务服务

    提供Agent发布流水线的完整管理能力，实现：
    Create → Test → Evaluation → Approval → Release → Deploy → Observe → Rollback

    核心规则：
    - 所有Agent发布必须经过Pipeline
    - 禁止绕过Evaluation直接发布
    - 评估不达标时Pipeline自动失败

    Attributes:
        repository: 流水线仓储实例
        event_bus: 事件总线实例（可选）
    """

    def __init__(
        self,
        repository: AgentPipelineRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        """初始化Pipeline服务

        Args:
            repository: 流水线仓储实例
            event_bus: 事件总线实例
        """
        self.repository = repository
        self.event_bus = event_bus

    # =========================================================================
    # 流水线管理
    # =========================================================================

    async def start_release_pipeline(
        self,
        agent_id: str,
        version_id: str,
        operator: str | None = None,
        tenant_id: str | None = None,
    ) -> AgentPipeline:
        """启动发布流水线

        创建并启动一个完整的Agent发布流水线。

        Args:
            agent_id: Agent标识
            version_id: 版本标识
            operator: 操作者标识
            tenant_id: 租户标识

        Returns:
            创建的流水线实体

        Raises:
            ValidationException: 参数校验失败
            BusinessRuleViolationException: 已有运行中的流水线
        """
        if not agent_id or not version_id:
            raise ValidationException(message="agent_id和version_id不能为空")

        # 检查是否已有运行中的流水线
        existing = await self.repository.find_latest_pipeline(agent_id, version_id)
        if existing and existing.status == PipelineStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="PIPELINE_ALREADY_RUNNING",
                message=f"Agent [{agent_id}] 版本 [{version_id}] 已有运行中的流水线 [{existing.id}]",
            )

        # 创建流水线
        pipeline = AgentPipeline(
            agent_id=agent_id,
            version_id=version_id,
            tenant_id=tenant_id,
            created_by=operator,
        )
        pipeline.initialize_steps(operator)
        pipeline.start(operator)

        saved_pipeline = await self.repository.save_pipeline(pipeline)
        await self.repository.save_steps(pipeline.steps)

        logger.info(
            "发布流水线已启动: pipeline_id=%s, agent_id=%s, version_id=%s",
            saved_pipeline.id,
            agent_id,
            version_id,
        )

        # 发布事件
        await self._publish_event(
            "agent.pipeline.started",
            {
                "pipeline_id": saved_pipeline.id,
                "agent_id": agent_id,
                "version_id": version_id,
            },
        )

        return saved_pipeline

    async def get_pipeline(self, pipeline_id: str) -> AgentPipeline:
        """获取流水线详情

        Args:
            pipeline_id: 流水线标识

        Returns:
            流水线实体

        Raises:
            ResourceNotFoundException: 流水线不存在
        """
        pipeline = await self.repository.find_pipeline_by_id(pipeline_id)
        if pipeline is None:
            raise ResourceNotFoundException(
                resource_type="Pipeline",
                resource_id=pipeline_id,
            )
        # 加载步骤
        steps = await self.repository.find_steps_by_pipeline_id(pipeline_id)
        pipeline.steps = steps
        return pipeline

    async def list_pipelines(
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
        return await self.repository.find_all_pipelines(pagination, tenant_id, filters)

    # =========================================================================
    # 阶段执行
    # =========================================================================

    async def execute_current_stage(
        self,
        pipeline_id: str,
        gate_passed: bool = True,
        result_data: dict | None = None,
        operator: str | None = None,
    ) -> AgentPipeline:
        """执行当前阶段

        完成当前阶段并推进到下一阶段。评估阶段必须通过质量门禁。

        Args:
            pipeline_id: 流水线标识
            gate_passed: 是否通过质量门禁
            result_data: 阶段执行结果数据
            operator: 操作者标识

        Returns:
            更新后的流水线实体

        Raises:
            ResourceNotFoundException: 流水线不存在
            BusinessRuleViolationException: 流水线状态不允许执行
        """
        pipeline = await self.get_pipeline(pipeline_id)

        if pipeline.status != PipelineStatus.RUNNING:
            raise BusinessRuleViolationException(
                rule="PIPELINE_NOT_RUNNING",
                message=f"流水线状态为 {pipeline.status.value}，只有运行中的流水线才能执行",
            )

        current_step = pipeline.get_current_step()
        if current_step is None:
            raise BusinessRuleViolationException(
                rule="PIPELINE_NO_CURRENT_STEP",
                message="流水线没有当前执行步骤",
            )

        # 评估阶段的门禁强制检查
        if current_step.stage == PipelineStage.EVALUATION and not gate_passed:
            current_step.fail("评估未通过质量门禁", operator)
            pipeline.fail_current_stage("评估未通过质量门禁", operator)
            await self._save_pipeline_state(pipeline)
            await self._publish_event(
                "agent.pipeline.evaluation.failed",
                {"pipeline_id": pipeline.id, "agent_id": pipeline.agent_id},
            )
            return pipeline

        # 完成当前步骤
        current_step.complete(gate_passed, result_data, operator)

        # 推进到下一阶段
        next_stage = pipeline.advance_to_next_stage(operator)

        await self._save_pipeline_state(pipeline)

        if next_stage:
            logger.info(
                "流水线推进: pipeline_id=%s, stage=%s -> %s",
                pipeline_id,
                current_step.stage.value,
                next_stage.value,
            )
        else:
            logger.info("流水线已完成: pipeline_id=%s", pipeline_id)
            await self._publish_event(
                "agent.pipeline.completed",
                {"pipeline_id": pipeline.id, "agent_id": pipeline.agent_id},
            )

        return pipeline

    # =========================================================================
    # 审批
    # =========================================================================

    async def approve_release(
        self,
        pipeline_id: str,
        reviewer: str,
        notes: str = "",
        operator: str | None = None,
    ) -> AgentPipeline:
        """批准发布

        在审批阶段批准Agent发布。

        Args:
            pipeline_id: 流水线标识
            reviewer: 审批者标识
            notes: 审批意见
            operator: 操作者标识

        Returns:
            更新后的流水线实体

        Raises:
            ResourceNotFoundException: 流水线不存在
            BusinessRuleViolationException: 当前不是审批阶段
        """
        pipeline = await self.get_pipeline(pipeline_id)

        current_step = pipeline.get_current_step()
        if current_step is None or current_step.stage != PipelineStage.APPROVAL:
            raise BusinessRuleViolationException(
                rule="PIPELINE_NOT_IN_APPROVAL",
                message="流水线当前不在审批阶段",
            )

        current_step.complete(
            gate_passed=True,
            result_data={
                "reviewer": reviewer,
                "notes": notes,
                "decision": "approved",
            },
            operator=operator,
        )

        pipeline.advance_to_next_stage(operator)
        await self._save_pipeline_state(pipeline)

        logger.info(
            "流水线审批通过: pipeline_id=%s, reviewer=%s",
            pipeline_id,
            reviewer,
        )

        await self._publish_event(
            "agent.pipeline.approved",
            {
                "pipeline_id": pipeline.id,
                "agent_id": pipeline.agent_id,
                "reviewer": reviewer,
            },
        )

        return pipeline

    async def reject_release(
        self,
        pipeline_id: str,
        reviewer: str,
        reason: str,
        operator: str | None = None,
    ) -> AgentPipeline:
        """拒绝发布

        在审批阶段拒绝Agent发布。

        Args:
            pipeline_id: 流水线标识
            reviewer: 审批者标识
            reason: 拒绝原因
            operator: 操作者标识

        Returns:
            更新后的流水线实体
        """
        pipeline = await self.get_pipeline(pipeline_id)

        current_step = pipeline.get_current_step()
        if current_step is None or current_step.stage != PipelineStage.APPROVAL:
            raise BusinessRuleViolationException(
                rule="PIPELINE_NOT_IN_APPROVAL",
                message="流水线当前不在审批阶段",
            )

        current_step.fail(f"审批被拒绝: {reason}", operator)
        pipeline.fail_current_stage(f"审批被拒绝: {reason}", operator)
        await self._save_pipeline_state(pipeline)

        logger.info(
            "流水线审批拒绝: pipeline_id=%s, reviewer=%s, reason=%s",
            pipeline_id,
            reviewer,
            reason,
        )

        await self._publish_event(
            "agent.pipeline.rejected",
            {
                "pipeline_id": pipeline.id,
                "agent_id": pipeline.agent_id,
                "reviewer": reviewer,
                "reason": reason,
            },
        )

        return pipeline

    # =========================================================================
    # 部署
    # =========================================================================

    async def deploy_release(
        self,
        pipeline_id: str,
        environment: str = "dev",
        operator: str | None = None,
    ) -> AgentPipeline:
        """部署发布

        在部署阶段执行Agent部署。

        Args:
            pipeline_id: 流水线标识
            environment: 部署环境
            operator: 操作者标识

        Returns:
            更新后的流水线实体

        Raises:
            BusinessRuleViolationException: 当前不是部署阶段
        """
        pipeline = await self.get_pipeline(pipeline_id)

        current_step = pipeline.get_current_step()
        if current_step is None or current_step.stage != PipelineStage.DEPLOY:
            raise BusinessRuleViolationException(
                rule="PIPELINE_NOT_IN_DEPLOY",
                message="流水线当前不在部署阶段",
            )

        # 检查评估是否通过
        if not pipeline.is_evaluation_passed:
            raise BusinessRuleViolationException(
                rule="PIPELINE_EVALUATION_NOT_PASSED",
                message="评估阶段未通过质量门禁，禁止部署",
            )

        current_step.complete(
            gate_passed=True,
            result_data={"environment": environment, "status": "deployed"},
            operator=operator,
        )

        pipeline.advance_to_next_stage(operator)
        await self._save_pipeline_state(pipeline)

        logger.info(
            "流水线部署完成: pipeline_id=%s, environment=%s",
            pipeline_id,
            environment,
        )

        await self._publish_event(
            "agent.pipeline.deployed",
            {
                "pipeline_id": pipeline.id,
                "agent_id": pipeline.agent_id,
                "environment": environment,
            },
        )

        return pipeline

    # =========================================================================
    # 回滚
    # =========================================================================

    async def rollback_release(
        self,
        pipeline_id: str,
        reason: str = "",
        operator: str | None = None,
    ) -> AgentPipeline:
        """回滚发布

        触发流水线回滚。

        Args:
            pipeline_id: 流水线标识
            reason: 回滚原因
            operator: 操作者标识

        Returns:
            更新后的流水线实体
        """
        pipeline = await self.get_pipeline(pipeline_id)

        if pipeline.status in (PipelineStatus.PASSED, PipelineStatus.CANCELLED):
            raise BusinessRuleViolationException(
                rule="PIPELINE_ROLLBACK_TERMINAL",
                message=f"流水线状态为 {pipeline.status.value}，不能回滚",
            )

        pipeline.trigger_rollback(reason, operator)
        await self._save_pipeline_state(pipeline)

        logger.info("流水线已回滚: pipeline_id=%s, reason=%s", pipeline_id, reason)

        await self._publish_event(
            "agent.pipeline.rolled_back",
            {
                "pipeline_id": pipeline.id,
                "agent_id": pipeline.agent_id,
                "reason": reason,
            },
        )

        return pipeline

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _save_pipeline_state(self, pipeline: AgentPipeline) -> None:
        """保存流水线及其步骤状态

        Args:
            pipeline: 流水线实体
        """
        await self.repository.save_pipeline(pipeline)
        if pipeline.steps:
            await self.repository.save_steps(pipeline.steps)

    async def _publish_event(
        self,
        event_type: str,
        payload: dict,
    ) -> None:
        """发布事件到事件总线

        Args:
            event_type: 事件类型
            payload: 事件负载
        """
        if self.event_bus:
            await self.event_bus.publish(event_type, payload, source="agent_pipeline")
