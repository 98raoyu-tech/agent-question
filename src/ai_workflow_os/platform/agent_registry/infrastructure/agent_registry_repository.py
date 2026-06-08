"""
Agent Registry仓储实现

提供Agent注册实体和运行时信息的内存存储实现，后续替换为数据库持久化。
"""

import logging

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.agent_registration import AgentRegistration
from ..domain.agent_runtime_info import AgentRuntimeInfo
from ..domain.enums import FrameworkType

logger = logging.getLogger(__name__)


class AgentRegistryRepository:
    """Agent Registry仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。
    同时管理Agent注册信息和运行时信息。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._registrations: dict[str, AgentRegistration] = {}
        self._runtime_infos: dict[str, AgentRuntimeInfo] = {}

    async def find_registration_by_id(
        self,
        registration_id: str,
        tenant_id: str | None = None,
    ) -> AgentRegistration | None:
        """根据ID查找Agent注册信息

        Args:
            registration_id: Agent注册标识
            tenant_id: 租户标识

        Returns:
            Agent注册实体，未找到返回None
        """
        registration = self._registrations.get(registration_id)

        # 检查租户隔离
        if registration is not None and tenant_id is not None and registration.tenant_id != tenant_id:
            return None

        # 检查软删除
        if registration is not None and registration.is_deleted:
            return None

        return registration

    async def find_all_registrations(
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
        # 过滤未删除的注册信息
        registrations = [
            r for r in self._registrations.values()
            if not r.is_deleted
        ]

        # 租户过滤
        if tenant_id is not None:
            registrations = [r for r in registrations if r.tenant_id == tenant_id]

        # 应用过滤条件
        if filters:
            if "status" in filters:
                registrations = [r for r in registrations if r.status.value == filters["status"]]
            if "framework" in filters:
                registrations = [r for r in registrations if r.framework.value == filters["framework"]]
            if "owner_id" in filters:
                registrations = [r for r in registrations if r.owner_id == filters["owner_id"]]
            if "team_id" in filters:
                registrations = [r for r in registrations if r.team_id == filters["team_id"]]
            if "search" in filters and filters["search"]:
                search_term = filters["search"].lower()
                registrations = [
                    r for r in registrations
                    if search_term in r.name.lower() or search_term in r.description.lower()
                ]

        # 排序
        if pagination.sort_by and hasattr(AgentRegistration, pagination.sort_by):
            reverse = pagination.sort_order == "desc"
            registrations.sort(key=lambda r: getattr(r, pagination.sort_by, ""), reverse=reverse)
        else:
            registrations.sort(key=lambda r: r.created_at, reverse=True)

        # 计算总数
        total = len(registrations)

        # 分页
        start = pagination.offset
        end = start + pagination.page_size
        page_items = registrations[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_registration(self, registration: AgentRegistration) -> AgentRegistration:
        """保存Agent注册信息

        Args:
            registration: Agent注册实体

        Returns:
            保存后的Agent注册实体
        """
        self._registrations[registration.id] = registration
        logger.debug("Agent注册信息已保存: id=%s", registration.id)
        return registration

    async def delete_registration(
        self,
        registration_id: str,
        tenant_id: str | None = None,
    ) -> bool:
        """删除Agent注册信息（软删除）

        Args:
            registration_id: Agent注册标识
            tenant_id: 租户标识

        Returns:
            是否删除成功
        """
        registration = await self.find_registration_by_id(registration_id, tenant_id)
        if registration is None:
            return False

        registration.mark_deleted()
        logger.debug("Agent注册信息已删除: id=%s", registration_id)
        return True

    async def find_registrations_by_framework(
        self,
        framework: FrameworkType,
        tenant_id: str | None = None,
    ) -> list[AgentRegistration]:
        """根据框架类型查找Agent注册列表

        Args:
            framework: 框架类型
            tenant_id: 租户标识

        Returns:
            匹配的Agent注册列表
        """
        registrations = [
            r for r in self._registrations.values()
            if not r.is_deleted and r.framework == framework
        ]

        if tenant_id is not None:
            registrations = [r for r in registrations if r.tenant_id == tenant_id]

        return registrations

    async def find_runtime_info_by_id(
        self,
        runtime_info_id: str,
    ) -> AgentRuntimeInfo | None:
        """根据ID查找运行时信息

        Args:
            runtime_info_id: 运行时信息标识

        Returns:
            运行时信息实体，未找到返回None
        """
        runtime_info = self._runtime_infos.get(runtime_info_id)

        # 检查软删除
        if runtime_info is not None and runtime_info.is_deleted:
            return None

        return runtime_info

    async def save_runtime_info(self, runtime_info: AgentRuntimeInfo) -> AgentRuntimeInfo:
        """保存运行时信息

        Args:
            runtime_info: 运行时信息实体

        Returns:
            保存后的运行时信息实体
        """
        self._runtime_infos[runtime_info.id] = runtime_info
        logger.debug("运行时信息已保存: id=%s, instance_id=%s", runtime_info.id, runtime_info.instance_id)
        return runtime_info

    async def find_runtime_infos_by_registration_id(
        self,
        registration_id: str,
    ) -> list[AgentRuntimeInfo]:
        """根据注册ID查找关联的运行时信息列表

        Args:
            registration_id: Agent注册标识

        Returns:
            关联的运行时信息列表
        """
        return [
            r for r in self._runtime_infos.values()
            if not r.is_deleted and r.agent_registration_id == registration_id
        ]
