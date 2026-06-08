"""
成本仓储实现

提供成本使用记录和预算实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.cost_budget import CostBudget
from ..domain.cost_usage import CostUsage

logger = logging.getLogger(__name__)


class CostRepository:
    """成本仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._usages: dict[str, CostUsage] = {}
        self._budgets: dict[str, CostBudget] = {}

    # =========================================================================
    # 成本记录操作
    # =========================================================================

    async def save_usage(self, usage: CostUsage) -> CostUsage:
        """保存成本使用记录

        Args:
            usage: 成本使用记录

        Returns:
            保存后的记录
        """
        self._usages[usage.id] = usage
        return usage

    async def find_usages(
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
        usages = list(self._usages.values())

        if agent_id is not None:
            usages = [u for u in usages if u.agent_id == agent_id]

        usages.sort(key=lambda u: u.created_at, reverse=True)

        total = len(usages)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = usages[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    # =========================================================================
    # 预算操作
    # =========================================================================

    async def find_budget_by_id(self, budget_id: str) -> Optional[CostBudget]:
        """根据ID查找预算

        Args:
            budget_id: 预算标识

        Returns:
            预算实体，未找到返回None
        """
        return self._budgets.get(budget_id)

    async def find_budget_by_agent_id(
        self,
        agent_id: str,
    ) -> Optional[CostBudget]:
        """根据Agent标识查找活跃预算

        Args:
            agent_id: Agent标识

        Returns:
            匹配的预算实体，未找到返回None
        """
        for budget in self._budgets.values():
            if budget.agent_id == agent_id and not budget.is_deleted:
                return budget
        return None

    async def find_all_budgets(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[CostBudget]:
        """分页查询预算列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        budgets = list(self._budgets.values())

        if tenant_id is not None:
            budgets = [b for b in budgets if b.tenant_id == tenant_id]

        budgets.sort(key=lambda b: b.created_at, reverse=True)

        total = len(budgets)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = budgets[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_budget(self, budget: CostBudget) -> CostBudget:
        """保存预算

        Args:
            budget: 预算实体

        Returns:
            保存后的预算实体
        """
        self._budgets[budget.id] = budget
        return budget
