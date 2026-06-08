"""
Agent Ops 服务

提供Agent运维管理的完整业务逻辑，包括部署、事故、运维手册、SLA/SLO管理。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.deployment import Deployment
from ..domain.enums import (
    DeploymentStatus,
    DeploymentStrategy,
    Environment,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
)
from ..domain.incident import Incident, TimelineEntry
from ..domain.runbook import Runbook, RunbookExecution, RunbookStep
from ..domain.sla import SLA
from ..domain.slo import SLO
from ..infrastructure.agent_ops_repository import AgentOpsRepository

logger = logging.getLogger(__name__)


class AgentOpsService:
    """Agent运维管理服务

    提供Agent运维的完整生命周期管理，包括部署、事故处理、运维手册和SLA/SLO监控。

    Attributes:
        repository: AgentOps仓储实例
    """

    def __init__(self, repository: AgentOpsRepository) -> None:
        """初始化AgentOps服务

        Args:
            repository: AgentOps仓储实例
        """
        self.repository = repository

    # =============================================================================
    # 部署管理
    # =============================================================================

    async def create_deployment(
        self,
        agent_id: str,
        version_id: str,
        environment: Environment,
        strategy: DeploymentStrategy,
        config: Optional[dict[str, Any]] = None,
        operator: Optional[str] = None,
    ) -> Deployment:
        """创建部署

        Args:
            agent_id: Agent标识
            version_id: 版本标识
            environment: 部署环境
            strategy: 部署策略
            config: 部署配置
            operator: 操作者标识

        Returns:
            创建的部署实体

        Raises:
            ValidationException: 参数校验失败
        """
        # 参数校验
        if not agent_id:
            raise ValidationException(message="agent_id不能为空")
        if not version_id:
            raise ValidationException(message="version_id不能为空")

        deployment = Deployment(
            agent_id=agent_id,
            version_id=version_id,
            environment=environment,
            strategy=strategy,
            config=config or {},
            created_by=operator,
            updated_by=operator,
        )

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("部署创建成功: id=%s, agent=%s", saved_deployment.id, agent_id)

        return saved_deployment

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """获取部署详情

        Args:
            deployment_id: 部署标识

        Returns:
            部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.repository.find_deployment_by_id(deployment_id)
        if deployment is None:
            raise ResourceNotFoundException(resource_type="Deployment", resource_id=deployment_id)
        return deployment

    async def list_deployments(
        self,
        pagination: PaginatedRequest,
        agent_id: Optional[str] = None,
        environment: Optional[Environment] = None,
        status: Optional[DeploymentStatus] = None,
    ) -> PaginatedResponse[Deployment]:
        """分页查询部署列表

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤
            environment: 环境过滤
            status: 状态过滤

        Returns:
            分页响应结果
        """
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if environment:
            filters["environment"] = environment.value
        if status:
            filters["status"] = status.value

        return await self.repository.find_all_deployments(pagination, filters=filters)

    async def update_deployment(
        self,
        deployment_id: str,
        config: Optional[dict[str, Any]] = None,
        operator: Optional[str] = None,
    ) -> Deployment:
        """更新部署配置

        Args:
            deployment_id: 部署标识
            config: 部署配置
            operator: 操作者标识

        Returns:
            更新后的部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
            BusinessRuleViolationException: 部署状态不允许更新
        """
        deployment = await self.get_deployment(deployment_id)

        # 只有PENDING状态才能更新配置
        if deployment.status != DeploymentStatus.PENDING:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_UPDATE_STATUS",
                message=f"当前状态 {deployment.status.value} 不允许更新部署配置",
            )

        if config is not None:
            deployment.config = config

        deployment.touch(operator)
        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("部署更新成功: id=%s", deployment_id)

        return saved_deployment

    async def execute_deployment(
        self,
        deployment_id: str,
        operator: Optional[str] = None,
    ) -> Deployment:
        """执行部署

        Args:
            deployment_id: 部署标识
            operator: 操作者标识

        Returns:
            部署后的实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.get_deployment(deployment_id)
        deployment.deploy(operator)

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("部署执行成功: id=%s", deployment_id)

        return saved_deployment

    async def rollback_deployment(
        self,
        deployment_id: str,
        operator: Optional[str] = None,
    ) -> Deployment:
        """回滚部署

        Args:
            deployment_id: 部署标识
            operator: 操作者标识

        Returns:
            回滚后的部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.get_deployment(deployment_id)
        deployment.rollback(operator)

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("部署回滚成功: id=%s", deployment_id)

        return saved_deployment

    async def promote_canary(
        self,
        deployment_id: str,
        percentage: int,
        operator: Optional[str] = None,
    ) -> Deployment:
        """提升灰度发布比例

        Args:
            deployment_id: 部署标识
            percentage: 目标百分比
            operator: 操作者标识

        Returns:
            更新后的部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.get_deployment(deployment_id)
        deployment.promote_canary(percentage, operator)

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("灰度比例提升: id=%s, percentage=%d%%", deployment_id, percentage)

        return saved_deployment

    async def switch_blue_green(
        self,
        deployment_id: str,
        operator: Optional[str] = None,
    ) -> Deployment:
        """切换蓝绿部署槽位

        Args:
            deployment_id: 部署标识
            operator: 操作者标识

        Returns:
            更新后的部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.get_deployment(deployment_id)
        deployment.switch_blue_green(operator)

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("蓝绿槽位切换: id=%s, slot=%s", deployment_id, deployment.blue_green_active_slot)

        return saved_deployment

    async def update_deployment_health(
        self,
        deployment_id: str,
        health_status: HealthStatus,
        operator: Optional[str] = None,
    ) -> Deployment:
        """更新部署健康状态

        Args:
            deployment_id: 部署标识
            health_status: 健康状态
            operator: 操作者标识

        Returns:
            更新后的部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.get_deployment(deployment_id)
        deployment.update_health(health_status, operator)

        saved_deployment = await self.repository.save_deployment(deployment)
        logger.info("部署健康状态更新: id=%s, status=%s", deployment_id, health_status.value)

        return saved_deployment

    # =============================================================================
    # 事故管理
    # =============================================================================

    async def create_incident(
        self,
        agent_id: str,
        title: str,
        description: str,
        severity: IncidentSeverity,
        environment: Environment,
        operator: Optional[str] = None,
    ) -> Incident:
        """创建事故

        Args:
            agent_id: Agent标识
            title: 事故标题
            description: 事故描述
            severity: 严重程度
            environment: 发生环境
            operator: 操作者标识

        Returns:
            创建的事故实体

        Raises:
            ValidationException: 参数校验失败
        """
        # 参数校验
        if not title:
            raise ValidationException(message="事故标题不能为空")

        incident = Incident(
            agent_id=agent_id,
            title=title,
            description=description,
            severity=severity,
            environment=environment,
            created_by=operator,
            updated_by=operator,
        )

        # 添加初始时间线
        incident.add_timeline_entry(
            TimelineEntry(
                action="created",
                operator=operator,
                details={"message": "事故已创建"},
            ),
            operator,
        )

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故创建成功: id=%s, title=%s", saved_incident.id, title)

        return saved_incident

    async def get_incident(self, incident_id: str) -> Incident:
        """获取事故详情

        Args:
            incident_id: 事故标识

        Returns:
            事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.repository.find_incident_by_id(incident_id)
        if incident is None:
            raise ResourceNotFoundException(resource_type="Incident", resource_id=incident_id)
        return incident

    async def list_incidents(
        self,
        pagination: PaginatedRequest,
        agent_id: Optional[str] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
    ) -> PaginatedResponse[Incident]:
        """分页查询事故列表

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤
            severity: 严重程度过滤
            status: 状态过滤

        Returns:
            分页响应结果
        """
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if severity:
            filters["severity"] = severity.value
        if status:
            filters["status"] = status.value

        return await self.repository.find_all_incidents(pagination, filters=filters)

    async def assign_incident(
        self,
        incident_id: str,
        user: str,
        operator: Optional[str] = None,
    ) -> Incident:
        """分配事故

        Args:
            incident_id: 事故标识
            user: 目标用户标识
            operator: 操作者标识

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.get_incident(incident_id)
        incident.assign(user, operator)

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故分配成功: id=%s, assigned_to=%s", incident_id, user)

        return saved_incident

    async def investigate_incident(
        self,
        incident_id: str,
        operator: Optional[str] = None,
    ) -> Incident:
        """开始调查事故

        Args:
            incident_id: 事故标识
            operator: 操作者标识

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.get_incident(incident_id)
        incident.investigate(operator)

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故开始调查: id=%s", incident_id)

        return saved_incident

    async def mitigate_incident(
        self,
        incident_id: str,
        operator: Optional[str] = None,
    ) -> Incident:
        """缓解事故

        Args:
            incident_id: 事故标识
            operator: 操作者标识

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.get_incident(incident_id)
        incident.mitigate(operator)

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故已缓解: id=%s", incident_id)

        return saved_incident

    async def resolve_incident(
        self,
        incident_id: str,
        root_cause: str,
        resolution: str,
        operator: Optional[str] = None,
    ) -> Incident:
        """解决事故

        Args:
            incident_id: 事故标识
            root_cause: 根本原因
            resolution: 解决方案
            operator: 操作者标识

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.get_incident(incident_id)
        incident.resolve(root_cause, resolution, operator)

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故已解决: id=%s", incident_id)

        return saved_incident

    async def close_incident(
        self,
        incident_id: str,
        operator: Optional[str] = None,
    ) -> Incident:
        """关闭事故

        Args:
            incident_id: 事故标识
            operator: 操作者标识

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
        """
        incident = await self.get_incident(incident_id)
        incident.close(operator)

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故已关闭: id=%s", incident_id)

        return saved_incident

    async def update_incident_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        operator: Optional[str] = None,
        **kwargs: Any,
    ) -> Incident:
        """更新事故状态

        Args:
            incident_id: 事故标识
            new_status: 新状态
            operator: 操作者标识
            **kwargs: 额外参数（如root_cause, resolution）

        Returns:
            更新后的事故实体

        Raises:
            ResourceNotFoundException: 事故不存在
            BusinessRuleViolationException: 状态转换无效
        """
        incident = await self.get_incident(incident_id)

        # 根据目标状态执行相应的状态转换
        status_handlers = {
            IncidentStatus.INVESTIGATING: lambda: incident.investigate(operator),
            IncidentStatus.MITIGATED: lambda: incident.mitigate(operator),
            IncidentStatus.RESOLVED: lambda: incident.resolve(
                kwargs.get("root_cause", ""),
                kwargs.get("resolution", ""),
                operator,
            ),
            IncidentStatus.CLOSED: lambda: incident.close(operator),
        }

        handler = status_handlers.get(new_status)
        if handler is None:
            raise BusinessRuleViolationException(
                rule="INCIDENT_STATUS_TRANSITION",
                message=f"无效的状态转换到 {new_status.value}",
            )

        handler()

        saved_incident = await self.repository.save_incident(incident)
        logger.info("事故状态更新: id=%s, status=%s", incident_id, new_status.value)

        return saved_incident

    # =============================================================================
    # 运维手册管理
    # =============================================================================

    async def create_runbook(
        self,
        name: str,
        description: str,
        agent_id: str,
        trigger_condition: str,
        steps: Optional[list[dict[str, Any]]] = None,
        operator: Optional[str] = None,
    ) -> Runbook:
        """创建运维手册

        Args:
            name: 手册名称
            description: 手册描述
            agent_id: Agent标识
            trigger_condition: 触发条件
            steps: 步骤列表
            operator: 操作者标识

        Returns:
            创建的运维手册实体

        Raises:
            ValidationException: 参数校验失败
        """
        # 参数校验
        if not name:
            raise ValidationException(message="运维手册名称不能为空")

        runbook = Runbook(
            name=name,
            description=description,
            agent_id=agent_id,
            trigger_condition=trigger_condition,
            created_by=operator,
            updated_by=operator,
        )

        # 添加步骤
        if steps:
            for step_data in steps:
                step = RunbookStep(
                    step_id=step_data.get("step_id", ""),
                    title=step_data.get("title", ""),
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", "manual"),
                    command=step_data.get("command"),
                    expected_result=step_data.get("expected_result"),
                )
                runbook.add_step(step, operator)

        saved_runbook = await self.repository.save_runbook(runbook)
        logger.info("运维手册创建成功: id=%s, name=%s", saved_runbook.id, name)

        return saved_runbook

    async def get_runbook(self, runbook_id: str) -> Runbook:
        """获取运维手册详情

        Args:
            runbook_id: 运维手册标识

        Returns:
            运维手册实体

        Raises:
            ResourceNotFoundException: 运维手册不存在
        """
        runbook = await self.repository.find_runbook_by_id(runbook_id)
        if runbook is None:
            raise ResourceNotFoundException(resource_type="Runbook", resource_id=runbook_id)
        return runbook

    async def list_runbooks(
        self,
        pagination: PaginatedRequest,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[Runbook]:
        """分页查询运维手册列表

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤
            is_active: 是否激活过滤

        Returns:
            分页响应结果
        """
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if is_active is not None:
            filters["is_active"] = is_active

        return await self.repository.find_all_runbooks(pagination, filters=filters)

    async def execute_runbook(
        self,
        runbook_id: str,
        context: dict[str, Any],
        operator: Optional[str] = None,
    ) -> RunbookExecution:
        """执行运维手册

        Args:
            runbook_id: 运维手册标识
            context: 执行上下文
            operator: 操作者标识

        Returns:
            执行记录

        Raises:
            ResourceNotFoundException: 运维手册不存在
        """
        runbook = await self.get_runbook(runbook_id)
        execution = runbook.execute(context, operator)

        # 保存更新后的运行手册
        await self.repository.save_runbook(runbook)
        logger.info("运维手册执行成功: id=%s, execution_id=%s", runbook_id, execution.execution_id)

        return execution

    async def add_runbook_step(
        self,
        runbook_id: str,
        step: RunbookStep,
        operator: Optional[str] = None,
    ) -> Runbook:
        """添加运维手册步骤

        Args:
            runbook_id: 运维手册标识
            step: 步骤
            operator: 操作者标识

        Returns:
            更新后的运维手册实体

        Raises:
            ResourceNotFoundException: 运维手册不存在
        """
        runbook = await self.get_runbook(runbook_id)
        runbook.add_step(step, operator)

        saved_runbook = await self.repository.save_runbook(runbook)
        logger.info("运维手册步骤添加成功: id=%s", runbook_id)

        return saved_runbook

    async def activate_runbook(
        self,
        runbook_id: str,
        operator: Optional[str] = None,
    ) -> Runbook:
        """激活运维手册

        Args:
            runbook_id: 运维手册标识
            operator: 操作者标识

        Returns:
            更新后的运维手册实体

        Raises:
            ResourceNotFoundException: 运维手册不存在
        """
        runbook = await self.get_runbook(runbook_id)
        runbook.activate(operator)

        saved_runbook = await self.repository.save_runbook(runbook)
        logger.info("运维手册激活成功: id=%s", runbook_id)

        return saved_runbook

    async def deactivate_runbook(
        self,
        runbook_id: str,
        operator: Optional[str] = None,
    ) -> Runbook:
        """停用运维手册

        Args:
            runbook_id: 运维手册标识
            operator: 操作者标识

        Returns:
            更新后的运维手册实体

        Raises:
            ResourceNotFoundException: 运维手册不存在
        """
        runbook = await self.get_runbook(runbook_id)
        runbook.deactivate(operator)

        saved_runbook = await self.repository.save_runbook(runbook)
        logger.info("运维手册停用成功: id=%s", runbook_id)

        return saved_runbook

    # =============================================================================
    # SLA管理
    # =============================================================================

    async def create_sla(
        self,
        name: str,
        agent_id: str,
        target_uptime: float = 99.9,
        target_latency_p99_ms: float = 500.0,
        target_success_rate: float = 99.5,
        target_availability: float = 99.99,
        period_days: int = 30,
        operator: Optional[str] = None,
    ) -> SLA:
        """创建SLA

        Args:
            name: SLA名称
            agent_id: Agent标识
            target_uptime: 目标正常运行时间
            target_latency_p99_ms: 目标P99延迟
            target_success_rate: 目标成功率
            target_availability: 目标可用性
            period_days: 评估周期
            operator: 操作者标识

        Returns:
            创建的SLA实体

        Raises:
            ValidationException: 参数校验失败
        """
        # 参数校验
        if not name:
            raise ValidationException(message="SLA名称不能为空")

        sla = SLA(
            name=name,
            agent_id=agent_id,
            target_uptime=target_uptime,
            target_latency_p99_ms=target_latency_p99_ms,
            target_success_rate=target_success_rate,
            target_availability=target_availability,
            period_days=period_days,
            created_by=operator,
            updated_by=operator,
        )

        saved_sla = await self.repository.save_sla(sla)
        logger.info("SLA创建成功: id=%s, name=%s", saved_sla.id, name)

        return saved_sla

    async def get_sla(self, sla_id: str) -> SLA:
        """获取SLA详情

        Args:
            sla_id: SLA标识

        Returns:
            SLA实体

        Raises:
            ResourceNotFoundException: SLA不存在
        """
        sla = await self.repository.find_sla_by_id(sla_id)
        if sla is None:
            raise ResourceNotFoundException(resource_type="SLA", resource_id=sla_id)
        return sla

    async def list_slas(
        self,
        pagination: PaginatedRequest,
        agent_id: Optional[str] = None,
    ) -> PaginatedResponse[SLA]:
        """分页查询SLA列表

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤

        Returns:
            分页响应结果
        """
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id

        return await self.repository.find_all_slas(pagination, filters=filters)

    async def update_sla_metrics(
        self,
        sla_id: str,
        uptime: float,
        latency: float,
        success_rate: float,
        availability: float,
        operator: Optional[str] = None,
    ) -> SLA:
        """更新SLA指标

        Args:
            sla_id: SLA标识
            uptime: 正常运行时间
            latency: P99延迟
            success_rate: 成功率
            availability: 可用性
            operator: 操作者标识

        Returns:
            更新后的SLA实体

        Raises:
            ResourceNotFoundException: SLA不存在
        """
        sla = await self.get_sla(sla_id)
        sla.update_metrics(uptime, latency, success_rate, availability, operator)

        saved_sla = await self.repository.save_sla(sla)
        logger.info("SLA指标更新成功: id=%s, is_met=%s", sla_id, sla.is_met)

        return saved_sla

    # =============================================================================
    # SLO管理
    # =============================================================================

    async def create_slo(
        self,
        name: str,
        agent_id: str,
        sla_id: str,
        metric_name: str,
        target_value: float,
        period_days: int = 30,
        operator: Optional[str] = None,
    ) -> SLO:
        """创建SLO

        Args:
            name: SLO名称
            agent_id: Agent标识
            sla_id: 关联的SLA标识
            metric_name: 指标名称
            target_value: 目标值
            period_days: 评估周期
            operator: 操作者标识

        Returns:
            创建的SLO实体

        Raises:
            ValidationException: 参数校验失败
        """
        # 参数校验
        if not name:
            raise ValidationException(message="SLO名称不能为空")
        if not metric_name:
            raise ValidationException(message="metric_name不能为空")

        slo = SLO(
            name=name,
            agent_id=agent_id,
            sla_id=sla_id,
            metric_name=metric_name,
            target_value=target_value,
            period_days=period_days,
            created_by=operator,
            updated_by=operator,
        )

        saved_slo = await self.repository.save_slo(slo)
        logger.info("SLO创建成功: id=%s, name=%s", saved_slo.id, name)

        return saved_slo

    async def get_slo(self, slo_id: str) -> SLO:
        """获取SLO详情

        Args:
            slo_id: SLO标识

        Returns:
            SLO实体

        Raises:
            ResourceNotFoundException: SLO不存在
        """
        slo = await self.repository.find_slo_by_id(slo_id)
        if slo is None:
            raise ResourceNotFoundException(resource_type="SLO", resource_id=slo_id)
        return slo

    async def list_slos(
        self,
        pagination: PaginatedRequest,
        agent_id: Optional[str] = None,
        sla_id: Optional[str] = None,
    ) -> PaginatedResponse[SLO]:
        """分页查询SLO列表

        Args:
            pagination: 分页参数
            agent_id: Agent标识过滤
            sla_id: SLA标识过滤

        Returns:
            分页响应结果
        """
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if sla_id:
            filters["sla_id"] = sla_id

        return await self.repository.find_all_slos(pagination, filters=filters)

    async def update_slo_value(
        self,
        slo_id: str,
        value: float,
        operator: Optional[str] = None,
    ) -> SLO:
        """更新SLO当前值

        Args:
            slo_id: SLO标识
            value: 当前值
            operator: 操作者标识

        Returns:
            更新后的SLO实体

        Raises:
            ResourceNotFoundException: SLO不存在
        """
        slo = await self.get_slo(slo_id)
        slo.update_current_value(value, operator)

        saved_slo = await self.repository.save_slo(slo)
        logger.info(
            "SLO值更新成功: id=%s, value=%.2f, budget_remaining=%.2f%%",
            slo_id,
            value,
            slo.error_budget_remaining,
        )

        return saved_slo
