"""
Agent注册表实体

定义Agent注册信息的核心领域实体，管理Agent的注册、注销和状态维护。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from ...common.exceptions import BusinessRuleViolationException
from .enums import AgentOrgStatus, AgentRole


@dataclass
class AgentRegistryEntry(BaseEntity):
    """Agent注册表条目实体

    记录一个Agent在多智能体组织中的完整注册信息，包括角色、能力、状态和并发控制。

    Attributes:
        agent_id: Agent唯一标识
        agent_name: Agent名称
        agent_role: Agent角色
        capabilities: Agent能力列表
        status: Agent组织状态
        endpoint_url: Agent通信端点
        max_concurrent_tasks: 最大并发任务数
        current_task_count: 当前任务数
        metadata: 扩展元数据
    """

    agent_id: str = ""
    agent_name: str = ""
    agent_role: AgentRole = AgentRole.BACKEND_DEV
    capabilities: list[str] = field(default_factory=list)
    status: AgentOrgStatus = AgentOrgStatus.IDLE
    endpoint_url: str = ""
    max_concurrent_tasks: int = 5
    current_task_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def register(self, operator: Optional[str] = None) -> None:
        """注册Agent

        将Agent状态设置为IDLE，标记为已注册。
        重复注册检测由服务层负责。

        Args:
            operator: 操作者标识
        """
        self.status = AgentOrgStatus.IDLE
        self.touch(operator)

    def deregister(self, operator: Optional[str] = None) -> None:
        """注销Agent

        将Agent状态设置为OFFLINE，标记为已注销。

        Args:
            operator: 操作者标识

        Raises:
            BusinessRuleViolationException: Agent仍有未完成的任务
        """
        if self.current_task_count > 0:
            raise BusinessRuleViolationException(
                rule="AGENT_HAS_ACTIVE_TASKS",
                message=f"Agent [{self.agent_id}] 仍有 {self.current_task_count} 个活跃任务，无法注销",
            )
        self.status = AgentOrgStatus.OFFLINE
        self.touch(operator)

    def update_status(self, status: AgentOrgStatus, operator: Optional[str] = None) -> None:
        """更新Agent状态

        Args:
            status: 目标状态
            operator: 操作者标识
        """
        self.status = status
        self.touch(operator)

    def is_available(self) -> bool:
        """判断Agent是否可用

        Returns:
            Agent处于空闲且未被删除时返回True
        """
        return self.status == AgentOrgStatus.IDLE and not self.is_deleted

    def can_accept_task(self) -> bool:
        """判断Agent是否可以接受新任务

        Returns:
            Agent可用且未达到并发上限时返回True
        """
        return self.is_available() and self.current_task_count < self.max_concurrent_tasks

    def increment_task_count(self, operator: Optional[str] = None) -> None:
        """增加当前任务计数

        Args:
            operator: 操作者标识
        """
        self.current_task_count += 1
        if self.current_task_count >= self.max_concurrent_tasks:
            self.status = AgentOrgStatus.BUSY
        self.touch(operator)

    def decrement_task_count(self, operator: Optional[str] = None) -> None:
        """减少当前任务计数

        Args:
            operator: 操作者标识
        """
        self.current_task_count = max(0, self.current_task_count - 1)
        if self.current_task_count < self.max_concurrent_tasks and self.status == AgentOrgStatus.BUSY:
            self.status = AgentOrgStatus.IDLE
        self.touch(operator)
