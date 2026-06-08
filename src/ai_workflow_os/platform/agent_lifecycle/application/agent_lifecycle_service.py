"""
Agent Lifecycle服务

提供Agent生命周期管理的完整业务逻辑，包括CRUD操作、状态机转换、
版本管理、测试提交、评估提交、审批流程、部署和回滚。
"""

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_approval import AgentApproval
from ..domain.agent_definition import AgentLifecycleDefinition
from ..domain.agent_deployment import AgentDeployment
from ..domain.agent_evaluation import AgentEvaluation
from ..domain.agent_rollback import AgentRollback
from ..domain.agent_test_run import AgentTestRun
from ..domain.agent_version import AgentLifecycleVersion
from ..domain.enums import (
    AgentLifecycleState,
    ApprovalStatus,
    DeploymentEnvironment,
    DeploymentStatus,
    DeploymentStrategy,
    RollbackStatus,
    TestRunStatus,
    TestType,
)
from ..infrastructure.agent_lifecycle_repository import AgentLifecycleRepository

logger = logging.getLogger(__name__)


class AgentLifecycleService:
    """Agent生命周期业务服务

    提供Agent的完整生命周期管理能力，包括CRUD、状态转换、版本管理、
    测试、评估、审批、部署和回滚操作。

    Attributes:
        repository: 仓储实例
    """

    def __init__(self, repository: AgentLifecycleRepository) -> None:
        """初始化Agent Lifecycle服务

        Args:
            repository: 仓储实例
        """
        self.repository = repository

    # =========================================================================
    # Agent CRUD
    # =========================================================================

    async def create_agent(
        self,
        agent: AgentLifecycleDefinition,
        operator: Optional[str] = None,
    ) -> AgentLifecycleDefinition:
        """创建Agent

        Args:
            agent: Agent定义实体
            operator: 操作者标识

        Returns:
            创建后的Agent实体

        Raises:
            ValidationException: Agent名称为空
        """
        if not agent.name or not agent.name.strip():
            raise ValidationException(message="Agent名称不能为空")

        agent.created_by = operator
        agent.updated_by = operator
        saved_agent = await self.repository.save_agent(agent)
        logger.info("Agent创建成功: id=%s, name=%s", saved_agent.id, saved_agent.name)

        await self._create_version(saved_agent, "初始版本", operator)
        return saved_agent

    async def update_agent(
        self,
        agent_id: str,
        agent: AgentLifecycleDefinition,
        operator: Optional[str] = None,
    ) -> AgentLifecycleDefinition:
        """更新Agent

        Args:
            agent_id: Agent标识
            agent: 更新后的Agent定义
            operator: 操作者标识

        Returns:
            更新后的Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: Agent状态不允许更新
        """
        existing_agent = await self._get_agent_or_raise(agent_id)

        if existing_agent.lifecycle_state != AgentLifecycleState.DRAFT:
            raise BusinessRuleViolationException(
                rule="AGENT_UPDATE_STATUS",
                message=(
                    f"Agent当前状态为 {existing_agent.lifecycle_state.value}，"
                    "只有草稿状态的Agent才能更新"
                ),
            )

        existing_agent.name = agent.name
        existing_agent.description = agent.description
        existing_agent.owner_id = agent.owner_id
        existing_agent.team_id = agent.team_id
        existing_agent.tags = agent.tags
        existing_agent.metadata = agent.metadata
        existing_agent.touch(operator)

        saved_agent = await self.repository.save_agent(existing_agent)
        logger.info("Agent更新成功: id=%s", agent_id)
        return saved_agent

    async def get_agent(self, agent_id: str) -> AgentLifecycleDefinition:
        """获取Agent详情

        Args:
            agent_id: Agent标识

        Returns:
            Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        return await self._get_agent_or_raise(agent_id)

    async def list_agents(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> PaginatedResponse[AgentLifecycleDefinition]:
        """分页查询Agent列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_agents(pagination, tenant_id, filters)

    # =========================================================================
    # 状态转换
    # =========================================================================

    async def transition_state(
        self,
        agent_id: str,
        target_state: AgentLifecycleState,
        operator: Optional[str] = None,
    ) -> AgentLifecycleDefinition:
        """执行Agent生命周期状态转换

        验证状态机规则并执行转换。

        Args:
            agent_id: Agent标识
            target_state: 目标生命周期状态
            operator: 操作者标识

        Returns:
            更新后的Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: 状态转换不合法
        """
        agent = await self._get_agent_or_raise(agent_id)
        agent.transition_to(target_state, operator)
        saved_agent = await self.repository.save_agent(agent)
        logger.info(
            "Agent状态转换成功: id=%s, %s -> %s",
            agent_id,
            agent.lifecycle_state.value,
            target_state.value,
        )
        return saved_agent

    # =========================================================================
    # 版本管理
    # =========================================================================

    async def create_version(
        self,
        agent_id: str,
        change_log: str = "",
        operator: Optional[str] = None,
    ) -> AgentLifecycleVersion:
        """创建新版本

        Args:
            agent_id: Agent标识
            change_log: 变更日志
            operator: 操作者标识

        Returns:
            新创建的版本实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        agent = await self._get_agent_or_raise(agent_id)
        version = await self._create_version(agent, change_log, operator)

        agent.current_version_id = version.id
        agent.touch(operator)
        await self.repository.save_agent(agent)

        return version

    async def list_versions(
        self,
        agent_id: str,
        pagination: Optional[PaginatedRequest] = None,
    ) -> list[AgentLifecycleVersion]:
        """查询Agent的版本列表

        Args:
            agent_id: Agent标识
            pagination: 分页参数（可选）

        Returns:
            版本列表
        """
        versions = await self.repository.find_versions_by_agent_id(agent_id)
        versions.sort(key=lambda v: v.created_at, reverse=True)

        if pagination:
            start = pagination.offset
            end = start + pagination.page_size
            return versions[start:end]

        return versions

    # =========================================================================
    # 测试管理
    # =========================================================================

    async def submit_for_testing(
        self,
        version_id: str,
        test_name: str = "",
        test_type: TestType = TestType.UNIT,
        operator: Optional[str] = None,
    ) -> AgentTestRun:
        """提交版本进行测试

        创建测试运行记录，并将Agent状态转换为TESTING。

        Args:
            version_id: 版本标识
            test_name: 测试名称
            test_type: 测试类型
            operator: 操作者标识

        Returns:
            测试运行实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self._get_version_or_raise(version_id)

        test_run = AgentTestRun(
            agent_id=version.agent_id,
            version_id=version_id,
            test_name=test_name or f"Test-{version.version_number}",
            test_type=test_type,
            created_by=operator,
        )
        saved_test_run = await self.repository.save_test_run(test_run)

        agent = await self._get_agent_or_raise(version.agent_id)
        if agent.can_transition_to(AgentLifecycleState.TESTING):
            agent.transition_to(AgentLifecycleState.TESTING, operator)
            await self.repository.save_agent(agent)

        version.lifecycle_state = AgentLifecycleState.TESTING
        version.touch(operator)
        await self.repository.save_version(version)

        logger.info("版本提交测试: version_id=%s, test_name=%s", version_id, test_name)
        return saved_test_run

    # =========================================================================
    # 评估管理
    # =========================================================================

    async def submit_for_evaluation(
        self,
        version_id: str,
        evaluation_name: str = "",
        operator: Optional[str] = None,
    ) -> AgentEvaluation:
        """提交版本进行评估

        创建评估记录，并将Agent状态转换为EVALUATION。

        Args:
            version_id: 版本标识
            evaluation_name: 评估名称
            operator: 操作者标识

        Returns:
            评估实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self._get_version_or_raise(version_id)

        evaluation = AgentEvaluation(
            agent_id=version.agent_id,
            version_id=version_id,
            evaluation_name=evaluation_name or f"Evaluation-{version.version_number}",
            created_by=operator,
        )
        saved_evaluation = await self.repository.save_evaluation(evaluation)

        agent = await self._get_agent_or_raise(version.agent_id)
        if agent.can_transition_to(AgentLifecycleState.EVALUATION):
            agent.transition_to(AgentLifecycleState.EVALUATION, operator)
            await self.repository.save_agent(agent)

        version.lifecycle_state = AgentLifecycleState.EVALUATION
        version.touch(operator)
        await self.repository.save_version(version)

        logger.info("版本提交评估: version_id=%s, evaluation_name=%s", version_id, evaluation_name)
        return saved_evaluation

    # =========================================================================
    # 审批管理
    # =========================================================================

    async def submit_for_approval(
        self,
        version_id: str,
        requested_by: str,
        operator: Optional[str] = None,
    ) -> AgentApproval:
        """提交版本进行审批

        创建审批请求，并将Agent状态转换为APPROVAL。

        Args:
            version_id: 版本标识
            requested_by: 请求者标识
            operator: 操作者标识

        Returns:
            审批实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self._get_version_or_raise(version_id)

        approval = AgentApproval(
            agent_id=version.agent_id,
            version_id=version_id,
            requested_by=requested_by,
            requested_at=datetime.now(timezone.utc),
            created_by=operator,
        )
        saved_approval = await self.repository.save_approval(approval)

        agent = await self._get_agent_or_raise(version.agent_id)
        if agent.can_transition_to(AgentLifecycleState.APPROVAL):
            agent.transition_to(AgentLifecycleState.APPROVAL, operator)
            await self.repository.save_agent(agent)

        version.lifecycle_state = AgentLifecycleState.APPROVAL
        version.touch(operator)
        await self.repository.save_version(version)

        logger.info("版本提交审批: version_id=%s, requested_by=%s", version_id, requested_by)
        return saved_approval

    async def approve_version(
        self,
        version_id: str,
        reviewer: str,
        notes: str = "",
        operator: Optional[str] = None,
    ) -> AgentApproval:
        """批准版本

        Args:
            version_id: 版本标识
            reviewer: 审批者标识
            notes: 审批意见
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 版本或审批不存在
            BusinessRuleViolationException: 审批状态不允许批准
        """
        version = await self._get_version_or_raise(version_id)
        approval = await self.repository.find_approval_by_version_id(version_id)
        if approval is None:
            raise ResourceNotFoundException(
                resource_type="审批记录",
                resource_id=version_id,
            )

        approval.approve(reviewer, notes, operator)
        await self.repository.save_approval(approval)

        version.approve(operator)
        await self.repository.save_version(version)

        logger.info("版本审批通过: version_id=%s, reviewer=%s", version_id, reviewer)
        return approval

    async def reject_version(
        self,
        version_id: str,
        reviewer: str,
        reason: str,
        operator: Optional[str] = None,
    ) -> AgentApproval:
        """拒绝版本

        Args:
            version_id: 版本标识
            reviewer: 审批者标识
            reason: 拒绝原因
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 版本或审批不存在
            BusinessRuleViolationException: 审批状态不允许拒绝
        """
        version = await self._get_version_or_raise(version_id)
        approval = await self.repository.find_approval_by_version_id(version_id)
        if approval is None:
            raise ResourceNotFoundException(
                resource_type="审批记录",
                resource_id=version_id,
            )

        approval.reject(reviewer, reason, operator)
        await self.repository.save_approval(approval)

        version.reject(reason, operator)
        await self.repository.save_version(version)

        logger.info("版本审批拒绝: version_id=%s, reviewer=%s", version_id, reviewer)
        return approval

    # =========================================================================
    # 部署管理
    # =========================================================================

    async def deploy_version(
        self,
        version_id: str,
        environment: DeploymentEnvironment = DeploymentEnvironment.DEV,
        deployment_strategy: DeploymentStrategy = DeploymentStrategy.DIRECT,
        operator: Optional[str] = None,
    ) -> AgentDeployment:
        """部署版本

        创建部署记录，执行部署，并将Agent状态转换为DEPLOYED。

        Args:
            version_id: 版本标识
            environment: 部署环境
            deployment_strategy: 部署策略
            operator: 操作者标识

        Returns:
            部署实体

        Raises:
            ResourceNotFoundException: 版本不存在
            BusinessRuleViolationException: 版本审批未通过
        """
        version = await self._get_version_or_raise(version_id)

        if version.approval_status != ApprovalStatus.APPROVED:
            raise BusinessRuleViolationException(
                rule="DEPLOYMENT_APPROVAL_REQUIRED",
                message=f"版本审批状态为 {version.approval_status.value}，只有已批准的版本才能部署",
            )

        deployment = AgentDeployment(
            agent_id=version.agent_id,
            version_id=version_id,
            environment=environment,
            deployment_strategy=deployment_strategy,
            created_by=operator,
        )
        deployment.deploy(operator)
        deployment.status = DeploymentStatus.ACTIVE
        saved_deployment = await self.repository.save_deployment(deployment)

        agent = await self._get_agent_or_raise(version.agent_id)
        if agent.can_transition_to(AgentLifecycleState.DEPLOYED):
            agent.transition_to(AgentLifecycleState.DEPLOYED, operator)
            agent.current_version_id = version_id
            await self.repository.save_agent(agent)

        logger.info(
            "版本部署成功: version_id=%s, environment=%s, strategy=%s",
            version_id,
            environment.value,
            deployment_strategy.value,
        )
        return saved_deployment

    async def rollback_deployment(
        self,
        deployment_id: str,
        reason: str = "",
        to_version_id: str = "",
        operator: Optional[str] = None,
    ) -> AgentRollback:
        """回滚部署

        执行部署回滚操作，并将Agent状态转换为ROLLED_BACK。

        Args:
            deployment_id: 部署标识
            reason: 回滚原因
            to_version_id: 回滚目标版本标识
            operator: 操作者标识

        Returns:
            回滚实体

        Raises:
            ResourceNotFoundException: 部署不存在
            BusinessRuleViolationException: 部署状态不允许回滚
        """
        deployment = await self.repository.find_deployment_by_id(deployment_id)
        if deployment is None:
            raise ResourceNotFoundException(
                resource_type="部署",
                resource_id=deployment_id,
            )

        deployment.rollback(operator)
        await self.repository.save_deployment(deployment)

        rollback = AgentRollback(
            agent_id=deployment.agent_id,
            from_version_id=deployment.version_id,
            to_version_id=to_version_id,
            reason=reason,
            created_by=operator,
        )
        rollback.start(operator)
        rollback.complete(operator)
        saved_rollback = await self.repository.save_rollback(rollback)

        agent = await self._get_agent_or_raise(deployment.agent_id)
        if agent.can_transition_to(AgentLifecycleState.ROLLED_BACK):
            agent.transition_to(AgentLifecycleState.ROLLED_BACK, operator)
            if to_version_id:
                agent.current_version_id = to_version_id
            await self.repository.save_agent(agent)

        logger.info(
            "部署回滚成功: deployment_id=%s, from=%s, to=%s",
            deployment_id,
            deployment.version_id,
            to_version_id,
        )
        return saved_rollback

    async def get_deployment_status(
        self,
        deployment_id: str,
    ) -> AgentDeployment:
        """获取部署状态

        Args:
            deployment_id: 部署标识

        Returns:
            部署实体

        Raises:
            ResourceNotFoundException: 部署不存在
        """
        deployment = await self.repository.find_deployment_by_id(deployment_id)
        if deployment is None:
            raise ResourceNotFoundException(
                resource_type="部署",
                resource_id=deployment_id,
            )
        return deployment

    async def list_deployments(
        self,
        agent_id: str,
        pagination: Optional[PaginatedRequest] = None,
    ) -> list[AgentDeployment]:
        """查询Agent的部署列表

        Args:
            agent_id: Agent标识
            pagination: 分页参数（可选）

        Returns:
            部署列表
        """
        deployments = await self.repository.find_deployments_by_agent_id(agent_id)
        deployments.sort(key=lambda d: d.created_at, reverse=True)

        if pagination:
            start = pagination.offset
            end = start + pagination.page_size
            return deployments[start:end]

        return deployments

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _get_agent_or_raise(self, agent_id: str) -> AgentLifecycleDefinition:
        """获取Agent或抛出异常

        Args:
            agent_id: Agent标识

        Returns:
            Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        agent = await self.repository.find_agent_by_id(agent_id)
        if agent is None:
            raise ResourceNotFoundException(
                resource_type="Agent",
                resource_id=agent_id,
            )
        return agent

    async def _get_version_or_raise(self, version_id: str) -> AgentLifecycleVersion:
        """获取版本或抛出异常

        Args:
            version_id: 版本标识

        Returns:
            版本实体

        Raises:
            ResourceNotFoundException: 版本不存在
        """
        version = await self.repository.find_version_by_id(version_id)
        if version is None:
            raise ResourceNotFoundException(
                resource_type="版本",
                resource_id=version_id,
            )
        return version

    async def _create_version(
        self,
        agent: AgentLifecycleDefinition,
        change_log: str = "",
        operator: Optional[str] = None,
    ) -> AgentLifecycleVersion:
        """创建Agent版本快照

        Args:
            agent: Agent实体
            change_log: 变更日志
            operator: 操作者标识

        Returns:
            版本实体
        """
        snapshot = asdict(agent)

        existing_versions = await self.repository.find_versions_by_agent_id(agent.id)
        for existing_version in existing_versions:
            if existing_version.is_current:
                existing_version.unset_current(operator)
                await self.repository.save_version(existing_version)

        version = AgentLifecycleVersion(
            agent_id=agent.id,
            version_number=f"v{len(existing_versions) + 1}",
            change_log=change_log,
            snapshot=snapshot,
            is_current=True,
            created_by=operator,
        )
        saved_version = await self.repository.save_version(version)
        logger.info(
            "Agent版本创建成功: agent_id=%s, version=%s",
            agent.id,
            saved_version.version_number,
        )
        return saved_version
