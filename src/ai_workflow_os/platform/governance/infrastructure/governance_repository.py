"""
治理仓储实现

提供策略和审计日志实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.audit_log import AuditLog
from ..domain.policy import Policy

logger = logging.getLogger(__name__)


class GovernanceRepository:
    """治理仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._policies: dict[str, Policy] = {}
        self._audit_logs: dict[str, AuditLog] = {}

    # =========================================================================
    # 策略操作
    # =========================================================================

    async def find_policy_by_id(self, policy_id: str) -> Optional[Policy]:
        """根据ID查找策略

        Args:
            policy_id: 策略标识

        Returns:
            策略实体，未找到返回None
        """
        policy = self._policies.get(policy_id)
        if policy is not None and policy.is_deleted:
            return None
        return policy

    async def find_all_policies(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[Policy]:
        """分页查询策略列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        policies = [p for p in self._policies.values() if not p.is_deleted]

        if tenant_id is not None:
            policies = [p for p in policies if p.tenant_id == tenant_id]

        policies.sort(key=lambda p: p.priority)

        total = len(policies)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = policies[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_policy(self, policy: Policy) -> Policy:
        """保存策略

        Args:
            policy: 策略实体

        Returns:
            保存后的策略实体
        """
        self._policies[policy.id] = policy
        return policy

    # =========================================================================
    # 审计日志操作
    # =========================================================================

    async def save_audit_log(self, audit_log: AuditLog) -> AuditLog:
        """保存审计日志

        Args:
            audit_log: 审计日志实体

        Returns:
            保存后的审计日志
        """
        self._audit_logs[audit_log.id] = audit_log
        return audit_log

    async def find_audit_logs(
        self,
        pagination: PaginatedRequest,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> PaginatedResponse[AuditLog]:
        """查询审计日志

        Args:
            pagination: 分页参数
            user_id: 用户标识
            resource_type: 资源类型

        Returns:
            分页响应结果
        """
        logs = list(self._audit_logs.values())

        if user_id is not None:
            logs = [l for l in logs if l.user_id == user_id]

        if resource_type is not None:
            logs = [l for l in logs if l.resource_type == resource_type]

        logs.sort(key=lambda l: l.created_at, reverse=True)

        total = len(logs)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = logs[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
