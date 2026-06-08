"""
治理服务

提供策略管理和审计日志的业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.audit_log import AuditLog
from ..domain.policy import Policy
from ..infrastructure.governance_repository import GovernanceRepository

logger = logging.getLogger(__name__)


class GovernanceService:
    """治理中心业务服务

    提供策略和审计日志的完整生命周期管理。

    Attributes:
        repository: 治理仓储实例
    """

    def __init__(self, repository: GovernanceRepository) -> None:
        """初始化治理服务

        Args:
            repository: 治理仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 策略管理
    # =========================================================================

    async def create_policy(
        self,
        policy: Policy,
        operator: Optional[str] = None,
    ) -> Policy:
        """创建策略

        Args:
            policy: 策略实体
            operator: 操作者标识

        Returns:
            创建后的策略实体

        Raises:
            ValidationException: 名称为空
        """
        if not policy.name or not policy.name.strip():
            raise ValidationException(message="策略名称不能为空")

        policy.created_by = operator
        policy.updated_by = operator

        saved_policy = await self.repository.save_policy(policy)
        logger.info("策略创建成功: id=%s, name=%s", saved_policy.id, saved_policy.name)

        return saved_policy

    async def get_policy(self, policy_id: str) -> Policy:
        """获取策略详情

        Args:
            policy_id: 策略标识

        Returns:
            策略实体

        Raises:
            ResourceNotFoundException: 策略不存在
        """
        policy = await self.repository.find_policy_by_id(policy_id)
        if policy is None:
            raise ResourceNotFoundException(resource_type="策略", resource_id=policy_id)
        return policy

    async def list_policies(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[Policy]:
        """查询策略列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_policies(pagination, tenant_id)

    async def delete_policy(self, policy_id: str, operator: Optional[str] = None) -> bool:
        """删除策略（软删除）

        Args:
            policy_id: 策略标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 策略不存在
        """
        policy = await self.repository.find_policy_by_id(policy_id)
        if policy is None:
            raise ResourceNotFoundException(resource_type="策略", resource_id=policy_id)

        policy.mark_deleted(operator)
        await self.repository.save_policy(policy)
        logger.info("策略删除成功: id=%s", policy_id)

        return True

    # =========================================================================
    # 审计日志管理
    # =========================================================================

    async def create_audit_log(
        self,
        audit_log: AuditLog,
    ) -> AuditLog:
        """创建审计日志

        Args:
            audit_log: 审计日志实体

        Returns:
            保存后的审计日志
        """
        saved_log = await self.repository.save_audit_log(audit_log)
        logger.debug(
            "审计日志创建: user=%s, action=%s, resource=%s/%s",
            audit_log.user_id,
            audit_log.action.value,
            audit_log.resource_type,
            audit_log.resource_id,
        )

        return saved_log

    async def list_audit_logs(
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
        return await self.repository.find_audit_logs(pagination, user_id, resource_type)
