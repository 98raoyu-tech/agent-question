"""
Agent Registry服务

提供Agent注册、更新、注销、运行时信息管理和心跳等业务逻辑。
"""

import logging
from datetime import UTC, datetime
from typing import Any

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_registration import AgentRegistration
from ..domain.agent_runtime_info import AgentRuntimeInfo
from ..domain.enums import AgentRegistryStatus, HealthStatus
from ..infrastructure.agent_registry_repository import AgentRegistryRepository

logger = logging.getLogger(__name__)


class AgentRegistryService:
    """Agent Registry业务服务

    提供Agent注册的完整生命周期管理，包括注册、更新、注销、
    运行时信息更新和心跳检测。

    Attributes:
        repository: Agent Registry仓储实例
    """

    def __init__(self, repository: AgentRegistryRepository) -> None:
        """初始化Agent Registry服务

        Args:
            repository: Agent Registry仓储实例
        """
        self.repository = repository

    async def register_agent(
        self,
        registration: AgentRegistration,
        operator: str | None = None,
    ) -> AgentRegistration:
        """注册Agent

        Args:
            registration: Agent注册实体
            operator: 操作者标识

        Returns:
            注册后的Agent实体

        Raises:
            ValidationException: Agent名称为空
        """
        # 校验Agent名称
        if not registration.name or not registration.name.strip():
            raise ValidationException(message="Agent名称不能为空")

        # 设置创建者
        registration.created_by = operator
        registration.updated_by = operator

        # 保存注册信息
        saved_registration = await self.repository.save_registration(registration)
        logger.info(
            "Agent注册成功: id=%s, name=%s, framework=%s",
            saved_registration.id,
            saved_registration.name,
            saved_registration.framework.value,
        )

        return saved_registration

    async def update_agent(
        self,
        registration_id: str,
        updates: dict[str, Any],
        operator: str | None = None,
    ) -> AgentRegistration:
        """更新Agent注册信息

        Args:
            registration_id: Agent注册标识
            updates: 需要更新的字段字典
            operator: 操作者标识

        Returns:
            更新后的Agent实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        # 查找现有Agent注册信息
        existing_registration = await self.repository.find_registration_by_id(registration_id)
        if existing_registration is None:
            raise ResourceNotFoundException(resource_type="AgentRegistration", resource_id=registration_id)

        # 应用更新字段
        updatable_fields = [
            "name", "description", "version", "framework", "model_name",
            "owner_id", "team_id", "endpoint", "tags", "metadata", "capabilities",
        ]
        for field_name in updatable_fields:
            if field_name in updates:
                setattr(existing_registration, field_name, updates[field_name])

        existing_registration.touch(operator)

        # 保存更新
        saved_registration = await self.repository.save_registration(existing_registration)
        logger.info("Agent注册信息更新成功: id=%s", registration_id)

        return saved_registration

    async def get_agent(self, registration_id: str) -> AgentRegistration:
        """获取Agent注册详情

        Args:
            registration_id: Agent注册标识

        Returns:
            Agent注册实体

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        registration = await self.repository.find_registration_by_id(registration_id)
        if registration is None:
            raise ResourceNotFoundException(resource_type="AgentRegistration", resource_id=registration_id)
        return registration

    async def list_agents(
        self,
        pagination: PaginatedRequest,
        tenant_id: str | None = None,
        filters: dict | None = None,
    ) -> PaginatedResponse[AgentRegistration]:
        """分页查询Agent注册列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识
            filters: 过滤条件

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_registrations(pagination, tenant_id, filters)

    async def deregister_agent(
        self,
        registration_id: str,
        operator: str | None = None,
    ) -> bool:
        """注销Agent（软删除）

        Args:
            registration_id: Agent注册标识
            operator: 操作者标识

        Returns:
            是否注销成功

        Raises:
            ResourceNotFoundException: Agent不存在
            BusinessRuleViolationException: Agent处于活跃状态不允许注销
        """
        registration = await self.repository.find_registration_by_id(registration_id)
        if registration is None:
            raise ResourceNotFoundException(resource_type="AgentRegistration", resource_id=registration_id)

        # 活跃状态的Agent需要先停用再注销
        if registration.status == AgentRegistryStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="AGENT_DEREGISTER_STATUS",
                message="活跃状态的Agent不能直接注销，请先停用",
            )

        registration.mark_deleted(operator)
        await self.repository.save_registration(registration)
        logger.info("Agent注销成功: id=%s", registration_id)

        return True

    async def update_runtime_info(
        self,
        runtime_info: AgentRuntimeInfo,
        operator: str | None = None,
    ) -> AgentRuntimeInfo:
        """更新Agent运行时信息

        Args:
            runtime_info: 运行时信息实体
            operator: 操作者标识

        Returns:
            保存后的运行时信息实体

        Raises:
            ResourceNotFoundException: 关联的Agent注册信息不存在
        """
        # 校验关联的注册信息是否存在
        registration = await self.repository.find_registration_by_id(runtime_info.agent_registration_id)
        if registration is None:
            raise ResourceNotFoundException(
                resource_type="AgentRegistration",
                resource_id=runtime_info.agent_registration_id,
            )

        runtime_info.created_by = operator or runtime_info.created_by
        runtime_info.updated_by = operator
        saved_runtime_info = await self.repository.save_runtime_info(runtime_info)
        logger.info(
            "运行时信息更新成功: registration_id=%s, instance_id=%s",
            runtime_info.agent_registration_id,
            runtime_info.instance_id,
        )

        return saved_runtime_info

    async def get_runtime_infos(self, registration_id: str) -> list[AgentRuntimeInfo]:
        """获取Agent关联的所有运行时信息

        Args:
            registration_id: Agent注册标识

        Returns:
            运行时信息列表

        Raises:
            ResourceNotFoundException: Agent不存在
        """
        # 校验注册信息是否存在
        registration = await self.repository.find_registration_by_id(registration_id)
        if registration is None:
            raise ResourceNotFoundException(resource_type="AgentRegistration", resource_id=registration_id)

        return await self.repository.find_runtime_infos_by_registration_id(registration_id)

    async def heartbeat(
        self,
        registration_id: str,
        instance_id: str,
    ) -> AgentRuntimeInfo:
        """Agent实例心跳

        更新指定实例的最近心跳时间，若实例不存在则创建新的运行时信息。

        Args:
            registration_id: Agent注册标识
            instance_id: 运行实例标识

        Returns:
            更新后的运行时信息实体

        Raises:
            ResourceNotFoundException: Agent注册信息不存在
        """
        # 校验注册信息是否存在
        registration = await self.repository.find_registration_by_id(registration_id)
        if registration is None:
            raise ResourceNotFoundException(resource_type="AgentRegistration", resource_id=registration_id)

        # 查找已有的运行时信息
        runtime_infos = await self.repository.find_runtime_infos_by_registration_id(registration_id)
        existing_info = next(
            (info for info in runtime_infos if info.instance_id == instance_id),
            None,
        )

        if existing_info is not None:
            # 更新已有实例的心跳
            existing_info.last_heartbeat = datetime.now(UTC)
            existing_info.status = HealthStatus.HEALTHY
            existing_info.touch()
            saved_info = await self.repository.save_runtime_info(existing_info)
        else:
            # 创建新的运行时信息
            new_info = AgentRuntimeInfo(
                agent_registration_id=registration_id,
                instance_id=instance_id,
                last_heartbeat=datetime.now(UTC),
                status=HealthStatus.HEALTHY,
            )
            saved_info = await self.repository.save_runtime_info(new_info)

        logger.debug("心跳更新成功: registration_id=%s, instance_id=%s", registration_id, instance_id)
        return saved_info
