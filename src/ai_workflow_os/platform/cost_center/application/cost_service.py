"""
成本服务

提供成本记录和预算管理的业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.cost_alert import AlertSeverity, AlertTargetType, AlertType, CostAlert
from ..domain.cost_budget import CostBudget
from ..domain.cost_usage import CostUsage
from ..infrastructure.cost_repository import CostRepository

logger = logging.getLogger(__name__)


class CostService:
    """成本中心业务服务

    提供成本记录和预算的完整生命周期管理。

    Attributes:
        repository: 成本仓储实例
    """

    def __init__(self, repository: CostRepository) -> None:
        """初始化成本服务

        Args:
            repository: 成本仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 成本记录管理
    # =========================================================================

    async def record_usage(
        self,
        usage: CostUsage,
        operator: Optional[str] = None,
    ) -> CostUsage:
        """记录成本使用

        Args:
            usage: 成本使用记录
            operator: 操作者标识

        Returns:
            保存后的记录
        """
        usage.created_by = operator
        usage.updated_by = operator

        saved_usage = await self.repository.save_usage(usage)
        logger.info(
            "成本记录成功: agent_id=%s, type=%s, amount=%s",
            usage.agent_id,
            usage.cost_type.value,
            usage.amount,
        )

        return saved_usage

    async def list_usages(
        self,
        agent_id: Optional[str],
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[CostUsage]:
        """查询成本使用记录

        Args:
            agent_id: Agent标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_usages(agent_id, pagination)

    # =========================================================================
    # 预算管理
    # =========================================================================

    async def create_budget(
        self,
        budget: CostBudget,
        operator: Optional[str] = None,
    ) -> CostBudget:
        """创建预算

        Args:
            budget: 预算实体
            operator: 操作者标识

        Returns:
            创建后的预算实体

        Raises:
            ValidationException: 名称为空
        """
        if not budget.name or not budget.name.strip():
            raise ValidationException(message="预算名称不能为空")

        budget.created_by = operator
        budget.updated_by = operator

        saved_budget = await self.repository.save_budget(budget)
        logger.info("预算创建成功: id=%s, name=%s", saved_budget.id, saved_budget.name)

        return saved_budget

    async def get_budget(self, budget_id: str) -> CostBudget:
        """获取预算详情

        Args:
            budget_id: 预算标识

        Returns:
            预算实体

        Raises:
            ResourceNotFoundException: 预算不存在
        """
        budget = await self.repository.find_budget_by_id(budget_id)
        if budget is None:
            raise ResourceNotFoundException(resource_type="预算", resource_id=budget_id)
        return budget

    async def list_budgets(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[CostBudget]:
        """查询预算列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_budgets(pagination, tenant_id)

    # =========================================================================
    # 预算检查与配额管理
    # =========================================================================

    async def check_budget(
        self,
        agent_id: str,
        estimated_cost: float,
    ) -> bool:
        """检查Agent是否有足够预算

        Args:
            agent_id: Agent标识
            estimated_cost: 预估成本

        Returns:
            是否有足够预算

        Raises:
            ResourceNotFoundException: 未找到关联预算
        """
        # 查找该Agent关联的活跃预算
        budget = await self.repository.find_budget_by_agent_id(agent_id)
        if budget is None:
            raise ResourceNotFoundException(
                resource_type="预算",
                resource_id=f"agent_id={agent_id}",
            )

        has_budget = budget.remaining_amount >= estimated_cost
        if not has_budget:
            logger.warning(
                "预算不足: agent_id=%s, 预估成本=%.2f, 剩余预算=%.2f",
                agent_id,
                estimated_cost,
                budget.remaining_amount,
            )
        return has_budget

    async def send_budget_alert(
        self,
        budget_id: str,
        operator: Optional[str] = None,
    ) -> CostAlert:
        """发送预算告警

        当预算使用率超过告警阈值时生成告警记录。

        Args:
            budget_id: 预算标识
            operator: 操作者标识

        Returns:
            生成的告警实体

        Raises:
            ResourceNotFoundException: 预算不存在
        """
        budget = await self.get_budget(budget_id)

        # 根据使用百分比确定告警严重级别
        usage_pct = budget.usage_percentage
        if usage_pct >= 100:
            severity = AlertSeverity.CRITICAL
            message = f"预算 [{budget.name}] 已超出，当前使用率: {usage_pct:.1f}%"
        elif usage_pct >= budget.alert_threshold:
            severity = AlertSeverity.WARNING
            message = f"预算 [{budget.name}] 即将超出，当前使用率: {usage_pct:.1f}%"
        else:
            severity = AlertSeverity.INFO
            message = f"预算 [{budget.name}] 使用率: {usage_pct:.1f}%"

        # 创建告警记录
        alert = CostAlert(
            budget_id=budget.id,
            target_id=budget.agent_id or budget.id,
            target_type=AlertTargetType.AGENT if budget.agent_id else AlertTargetType.TENANT,
            alert_type=AlertType.THRESHOLD,
            severity=severity,
            message=message,
            threshold_percentage=budget.alert_threshold,
            current_percentage=usage_pct,
            created_by=operator,
            updated_by=operator,
        )

        logger.warning(
            "预算告警已发送: budget_id=%s, severity=%s, usage=%.1f%%",
            budget_id,
            severity.value,
            usage_pct,
        )
        return alert

    async def enforce_quota(
        self,
        agent_id: str,
        cost_amount: float,
    ) -> bool:
        """执行配额限制

        检查Agent配额是否允许本次消费，若允许则记录使用量。

        Args:
            agent_id: Agent标识
            cost_amount: 本次消费金额

        Returns:
            是否允许消费

        Raises:
            ResourceNotFoundException: 未找到关联预算
            ValidationException: 消费金额无效
        """
        if cost_amount <= 0:
            raise ValidationException(message="消费金额必须为正数")

        # 查找该Agent关联的活跃预算
        budget = await self.repository.find_budget_by_agent_id(agent_id)
        if budget is None:
            raise ResourceNotFoundException(
                resource_type="配额",
                resource_id=f"agent_id={agent_id}",
            )

        # 检查预算状态是否允许消费
        if budget.status.value == "suspended":
            logger.warning(
                "配额已暂停，拒绝消费: agent_id=%s, amount=%.2f",
                agent_id,
                cost_amount,
            )
            return False

        # 检查剩余预算是否充足
        if budget.remaining_amount < cost_amount:
            logger.warning(
                "配额不足，拒绝消费: agent_id=%s, 需要=%.2f, 剩余=%.2f",
                agent_id,
                cost_amount,
                budget.remaining_amount,
            )
            return False

        # 记录使用量
        budget.add_usage(cost_amount, operator=agent_id)
        await self.repository.save_budget(budget)

        logger.info(
            "配额消费成功: agent_id=%s, amount=%.2f, 剩余=%.2f",
            agent_id,
            cost_amount,
            budget.remaining_amount,
        )
        return True
