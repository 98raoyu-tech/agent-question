"""
工具权限管理模块

管理工具的访问权限，支持基于角色和Agent的权限控制。
提供权限设置、检查、授予和撤销功能。
"""

from dataclasses import dataclass, field
from typing import Any
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class PermissionRule:
    """权限规则定义
    
    Attributes:
        tool_name: 工具名称
        allowed_roles: 允许访问的角色列表
        allowed_agents: 允许访问的Agent ID列表
        requires_approval: 是否需要审批
        risk_level: 风险等级（low/medium/high/critical）
    """
    tool_name: str
    allowed_roles: list[str] = field(default_factory=list)
    allowed_agents: list[str] = field(default_factory=list)
    requires_approval: bool = False
    risk_level: str = "low"


@dataclass
class PermissionResult:
    """权限检查结果
    
    Attributes:
        allowed: 是否允许访问
        reason: 检查结果原因说明
        requires_approval: 是否需要审批
    """
    allowed: bool
    reason: str = ""
    requires_approval: bool = False


class ToolPermissionManager:
    """工具权限管理器
    
    管理工具的访问权限，支持基于角色和Agent的权限控制。
    
    Attributes:
        permission_rules: 工具权限规则映射表，键为工具名称
        agent_permissions: Agent权限映射表，键为Agent ID，值为授权工具集合
    """
    
    def __init__(self) -> None:
        """初始化工具权限管理器"""
        self.permission_rules: dict[str, PermissionRule] = {}
        self.agent_permissions: dict[str, set[str]] = {}
        logger.info("工具权限管理器已初始化")
    
    def set_permission(self, tool_name: str, rule: PermissionRule) -> None:
        """设置工具权限
        
        Args:
            tool_name: 工具名称
            rule: 权限规则定义
        """
        # 更新工具名称以保持一致性
        rule.tool_name = tool_name
        self.permission_rules[tool_name] = rule
        
        logger.info(f"已设置工具 '{tool_name}' 的权限规则 (风险等级: {rule.risk_level})")
    
    def check_permission(
        self,
        agent_id: str,
        agent_type: str,
        tool_name: str
    ) -> PermissionResult:
        """检查权限
        
        Args:
            agent_id: Agent ID
            agent_type: Agent类型（角色）
            tool_name: 工具名称
            
        Returns:
            PermissionResult: 权限检查结果
        """
        # 获取工具权限规则
        rule = self.permission_rules.get(tool_name)
        
        # 如果没有设置权限规则，默认允许访问
        if not rule:
            return PermissionResult(
                allowed=True,
                reason="工具未设置权限规则，默认允许访问"
            )
        
        # 检查Agent是否在允许列表中
        if agent_id in rule.allowed_agents:
            return PermissionResult(
                allowed=True,
                reason=f"Agent '{agent_id}' 在工具允许列表中",
                requires_approval=rule.requires_approval
            )
        
        # 检查Agent类型是否在允许角色中
        if agent_type in rule.allowed_roles:
            return PermissionResult(
                allowed=True,
                reason=f"Agent类型 '{agent_type}' 在工具允许角色中",
                requires_approval=rule.requires_approval
            )
        
        # 检查Agent是否被单独授权
        agent_tools = self.agent_permissions.get(agent_id, set())
        if tool_name in agent_tools:
            return PermissionResult(
                allowed=True,
                reason=f"Agent '{agent_id}' 已被单独授权使用该工具",
                requires_approval=rule.requires_approval
            )
        
        # 权限不足
        return PermissionResult(
            allowed=False,
            reason=f"Agent '{agent_id}' (类型: {agent_type}) 无权使用工具 '{tool_name}'",
            requires_approval=rule.requires_approval
        )
    
    def grant_agent_permission(self, agent_id: str, tool_name: str) -> bool:
        """授予Agent工具权限
        
        Args:
            agent_id: Agent ID
            tool_name: 工具名称
            
        Returns:
            bool: 授予成功返回True，工具不存在返回False
        """
        # 检查工具是否有权限规则
        if tool_name not in self.permission_rules:
            logger.warning(f"工具 '{tool_name}' 未设置权限规则，无法授予")
            return False
        
        # 初始化Agent权限集合
        if agent_id not in self.agent_permissions:
            self.agent_permissions[agent_id] = set()
        
        # 授予权限
        self.agent_permissions[agent_id].add(tool_name)
        
        logger.info(f"已授予Agent '{agent_id}' 使用工具 '{tool_name}' 的权限")
        return True
    
    def revoke_agent_permission(self, agent_id: str, tool_name: str) -> bool:
        """撤销Agent工具权限
        
        Args:
            agent_id: Agent ID
            tool_name: 工具名称
            
        Returns:
            bool: 撤销成功返回True，Agent或工具权限不存在返回False
        """
        # 检查Agent是否有权限记录
        if agent_id not in self.agent_permissions:
            logger.warning(f"Agent '{agent_id}' 没有权限记录")
            return False
        
        # 检查Agent是否有该工具权限
        if tool_name not in self.agent_permissions[agent_id]:
            logger.warning(f"Agent '{agent_id}' 没有使用工具 '{tool_name}' 的权限")
            return False
        
        # 撤销权限
        self.agent_permissions[agent_id].remove(tool_name)
        
        # 如果Agent没有其他权限，移除记录
        if not self.agent_permissions[agent_id]:
            del self.agent_permissions[agent_id]
        
        logger.info(f"已撤销Agent '{agent_id}' 使用工具 '{tool_name}' 的权限")
        return True
    
    def get_agent_tools(self, agent_id: str) -> list[str]:
        """获取Agent可用工具列表
        
        Args:
            agent_id: Agent ID
            
        Returns:
            list: Agent可用的工具名称列表
        """
        # 获取Agent被单独授权的工具
        agent_tools = list(self.agent_permissions.get(agent_id, set()))
        
        # 获取所有未设置权限规则的工具（默认允许访问）
        for tool_name, rule in self.permission_rules.items():
            if tool_name not in agent_tools:
                # 如果工具未设置角色和Agent限制，也添加到列表
                if not rule.allowed_roles and not rule.allowed_agents:
                    agent_tools.append(tool_name)
        
        return sorted(agent_tools)
    
    def get_tool_permissions(self, tool_name: str) -> dict[str, Any] | None:
        """获取工具权限详情
        
        Args:
            tool_name: 工具名称
            
        Returns:
            dict: 工具权限详情，工具不存在返回None
        """
        rule = self.permission_rules.get(tool_name)
        if not rule:
            return None
        
        # 获取被授权使用该工具的Agent列表
        authorized_agents = [
            agent_id for agent_id, tools in self.agent_permissions.items()
            if tool_name in tools
        ]
        
        return {
            "tool_name": tool_name,
            "allowed_roles": rule.allowed_roles,
            "allowed_agents": rule.allowed_agents,
            "requires_approval": rule.requires_approval,
            "risk_level": rule.risk_level,
            "authorized_agents": authorized_agents
        }
    
    def list_all_permissions(self) -> list[dict[str, Any]]:
        """列出所有工具权限
        
        Returns:
            list: 所有工具的权限信息列表
        """
        permissions = []
        
        for tool_name in self.permission_rules:
            perm_info = self.get_tool_permissions(tool_name)
            if perm_info:
                permissions.append(perm_info)
        
        return permissions
    
    def get_statistics(self) -> dict[str, Any]:
        """获取权限统计信息
        
        Returns:
            dict: 权限统计信息
        """
        # 统计各风险等级的工具数量
        risk_counts: dict[str, int] = {}
        for rule in self.permission_rules.values():
            risk_counts[rule.risk_level] = risk_counts.get(rule.risk_level, 0) + 1
        
        # 统计需要审批的工具数量
        approval_required_count = sum(
            1 for rule in self.permission_rules.values()
            if rule.requires_approval
        )
        
        return {
            "total_tools": len(self.permission_rules),
            "total_agents_with_permissions": len(self.agent_permissions),
            "risk_level_counts": risk_counts,
            "approval_required_count": approval_required_count
        }