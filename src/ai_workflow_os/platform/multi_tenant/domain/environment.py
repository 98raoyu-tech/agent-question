"""
环境实体

定义资源环境的核心业务实体，包含项目归属、环境类型、配置和Agent部署管理等功能。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import ResourceEnvironment


@dataclass
class Environment(BaseEntity):
    """环境实体

    核心业务实体，描述一个资源环境的完整信息。

    Attributes:
        tenant_id: 所属租户标识
        project_id: 所属项目标识
        name: 环境名称
        environment_type: 环境类型
        config: 环境配置
        is_active: 是否激活
        deployed_agent_ids: 已部署的Agent标识列表
    """

    tenant_id: Optional[str] = None
    project_id: str = ""
    name: str = ""
    environment_type: ResourceEnvironment = ResourceEnvironment.DEV
    config: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    deployed_agent_ids: list[str] = field(default_factory=list)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活环境

        Args:
            operator: 操作者标识
        """
        self.is_active = True
        self.touch(operator)

    def deactivate(self, operator: Optional[str] = None) -> None:
        """停用环境

        Args:
            operator: 操作者标识
        """
        self.is_active = False
        self.touch(operator)

    def deploy_agent(self, agent_id: str, operator: Optional[str] = None) -> None:
        """部署Agent到环境

        Args:
            agent_id: Agent标识
            operator: 操作者标识
        """
        if agent_id not in self.deployed_agent_ids:
            self.deployed_agent_ids.append(agent_id)
            self.touch(operator)

    def undeploy_agent(self, agent_id: str, operator: Optional[str] = None) -> None:
        """从环境卸载Agent

        Args:
            agent_id: Agent标识
            operator: 操作者标识
        """
        if agent_id in self.deployed_agent_ids:
            self.deployed_agent_ids.remove(agent_id)
            self.touch(operator)
