"""
策略引擎模块

执行策略治理，支持动态策略规则。
提供策略的添加、移除、评估和冲突解决功能。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import asyncio
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """策略动作枚举
    
    定义策略匹配后可执行的动作类型。
    """
    ALLOW = "allow"                      # 允许操作
    DENY = "deny"                        # 拒绝操作
    REQUIRE_APPROVAL = "require_approval"  # 需要审批
    LOG_ONLY = "log_only"                # 仅记录日志


@dataclass
class PolicyRule:
    """策略规则定义
    
    Attributes:
        rule_id: 规则唯一标识
        name: 规则名称
        condition: 匹配条件，支持字符串表达式或字典配置
        action: 匹配后的动作
        priority: 优先级，数值越大优先级越高
        enabled: 是否启用
    """
    rule_id: str
    name: str
    condition: str | dict[str, Any]
    action: PolicyAction
    priority: int = 0
    enabled: bool = True


@dataclass
class PolicyResult:
    """策略评估结果
    
    Attributes:
        action: 最终执行的动作
        matched_rules: 匹配到的规则列表
        reason: 决策原因说明
    """
    action: PolicyAction
    matched_rules: list[str] = field(default_factory=list)
    reason: str = ""


class PolicyEngine:
    """策略引擎
    
    执行策略治理，支持动态策略规则的添加、移除和评估。
    
    Attributes:
        policies: 策略规则列表
    """
    
    def __init__(self) -> None:
        """初始化策略引擎"""
        self.policies: list[PolicyRule] = []
        logger.info("策略引擎已初始化")
    
    def add_policy(self, rule: PolicyRule) -> None:
        """添加策略
        
        Args:
            rule: 策略规则定义
        """
        # 检查规则ID是否已存在
        existing_rule = next(
            (r for r in self.policies if r.rule_id == rule.rule_id),
            None
        )
        
        if existing_rule:
            # 更新现有规则
            self.policies.remove(existing_rule)
            logger.info(f"更新策略规则: {rule.rule_id} ({rule.name})")
        
        self.policies.append(rule)
        
        # 按优先级排序（降序）
        self.policies.sort(key=lambda r: r.priority, reverse=True)
        
        logger.info(f"已添加策略规则: {rule.rule_id} ({rule.name}), 优先级: {rule.priority}")
    
    def remove_policy(self, rule_id: str) -> bool:
        """移除策略
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 移除成功返回True，规则不存在返回False
        """
        # 查找规则
        rule = next(
            (r for r in self.policies if r.rule_id == rule_id),
            None
        )
        
        if not rule:
            logger.warning(f"策略规则 '{rule_id}' 不存在")
            return False
        
        self.policies.remove(rule)
        logger.info(f"已移除策略规则: {rule_id} ({rule.name})")
        return True
    
    async def evaluate(self, action_context: dict[str, Any]) -> PolicyResult:
        """评估操作是否符合策略
        
        Args:
            action_context: 操作上下文信息
            
        Returns:
            PolicyResult: 策略评估结果
        """
        matched_rules: list[PolicyRule] = []
        
        # 遍历所有启用的策略规则
        for rule in self.policies:
            # 跳过未启用的规则
            if not rule.enabled:
                continue
            
            # 检查条件是否匹配
            if self._match_condition(rule.condition, action_context):
                matched_rules.append(rule)
                logger.debug(f"策略规则匹配: {rule.rule_id} ({rule.name})")
        
        # 如果没有匹配的规则，默认允许
        if not matched_rules:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                matched_rules=[],
                reason="无匹配策略规则，默认允许操作"
            )
        
        # 解决策略冲突
        return self._resolve_conflicts(matched_rules)
    
    def _match_condition(
        self,
        condition: str | dict[str, Any],
        context: dict[str, Any]
    ) -> bool:
        """匹配条件
        
        Args:
            condition: 匹配条件
            context: 操作上下文
            
        Returns:
            bool: 条件匹配返回True
        """
        # 字符串条件：简单的键值匹配
        if isinstance(condition, str):
            return self._evaluate_string_condition(condition, context)
        
        # 字典条件：结构化匹配
        if isinstance(condition, dict):
            return self._evaluate_dict_condition(condition, context)
        
        return False
    
    def _evaluate_string_condition(
        self,
        condition: str,
        context: dict[str, Any]
    ) -> bool:
        """评估字符串条件
        
        支持简单的表达式语法，如 "action == 'delete'" 或 "user.role == 'admin'"
        
        Args:
            condition: 条件表达式
            context: 操作上下文
            
        Returns:
            bool: 条件满足返回True
        """
        try:
            # 安全的字典，只包含上下文变量
            safe_dict = {"__builtins__": {}}
            safe_dict.update(context)
            
            # 评估表达式
            result = eval(condition, safe_dict)
            return bool(result)
        except Exception as e:
            logger.error(f"条件表达式评估失败: {condition}, 错误: {str(e)}")
            return False
    
    def _evaluate_dict_condition(
        self,
        condition: dict[str, Any],
        context: dict[str, Any]
    ) -> bool:
        """评估字典条件
        
        支持结构化的条件匹配，如 {"field": "user.role", "operator": "eq", "value": "admin"}
        
        Args:
            condition: 条件配置
            context: 操作上下文
            
        Returns:
            bool: 条件满足返回True
        """
        field_name = condition.get("field")
        operator = condition.get("operator", "eq")
        expected_value = condition.get("value")
        
        if not field_name:
            return False
        
        # 获取实际值
        actual_value = context.get(field_name)
        
        # 根据操作符进行比较
        if operator == "eq":
            return actual_value == expected_value
        elif operator == "ne":
            return actual_value != expected_value
        elif operator == "in":
            return actual_value in expected_value if expected_value else False
        elif operator == "not_in":
            return actual_value not in expected_value if expected_value else True
        elif operator == "contains":
            return expected_value in actual_value if actual_value else False
        elif operator == "gt":
            return actual_value > expected_value if actual_value is not None else False
        elif operator == "lt":
            return actual_value < expected_value if actual_value is not None else False
        elif operator == "gte":
            return actual_value >= expected_value if actual_value is not None else False
        elif operator == "lte":
            return actual_value <= expected_value if actual_value is not None else False
        
        logger.warning(f"不支持的操作符: {operator}")
        return False
    
    def _resolve_conflicts(self, matched_rules: list[PolicyRule]) -> PolicyResult:
        """解决策略冲突
        
        按优先级排序，使用最高优先级规则的动作。
        
        Args:
            matched_rules: 匹配到的规则列表（已按优先级排序）
            
        Returns:
            PolicyResult: 冲突解决后的结果
        """
        # 获取最高优先级规则（列表已按优先级降序排序）
        highest_priority_rule = matched_rules[0]
        
        # 收集所有匹配规则的ID
        matched_rule_ids = [rule.rule_id for rule in matched_rules]
        
        # 构建原因说明
        if len(matched_rules) > 1:
            reason = (
                f"匹配到 {len(matched_rules)} 条策略规则，"
                f"使用最高优先级规则 '{highest_priority_rule.rule_id}' "
                f"({highest_priority_rule.name}) 的决策"
            )
        else:
            reason = f"匹配策略规则 '{highest_priority_rule.rule_id}' ({highest_priority_rule.name})"
        
        return PolicyResult(
            action=highest_priority_rule.action,
            matched_rules=matched_rule_ids,
            reason=reason
        )
    
    def list_policies(self) -> list[dict[str, Any]]:
        """列出所有策略
        
        Returns:
            list: 策略信息列表
        """
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "condition": rule.condition,
                "action": rule.action.value,
                "priority": rule.priority,
                "enabled": rule.enabled
            }
            for rule in self.policies
        ]
    
    def enable_policy(self, rule_id: str) -> bool:
        """启用策略
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 启用成功返回True，规则不存在返回False
        """
        rule = next(
            (r for r in self.policies if r.rule_id == rule_id),
            None
        )
        
        if not rule:
            logger.warning(f"策略规则 '{rule_id}' 不存在")
            return False
        
        rule.enabled = True
        logger.info(f"已启用策略规则: {rule_id} ({rule.name})")
        return True
    
    def disable_policy(self, rule_id: str) -> bool:
        """禁用策略
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 禁用成功返回True，规则不存在返回False
        """
        rule = next(
            (r for r in self.policies if r.rule_id == rule_id),
            None
        )
        
        if not rule:
            logger.warning(f"策略规则 '{rule_id}' 不存在")
            return False
        
        rule.enabled = False
        logger.info(f"已禁用策略规则: {rule_id} ({rule.name})")
        return True
    
    def get_policy(self, rule_id: str) -> dict[str, Any] | None:
        """获取策略详情
        
        Args:
            rule_id: 规则ID
            
        Returns:
            dict: 策略详情，不存在返回None
        """
        rule = next(
            (r for r in self.policies if r.rule_id == rule_id),
            None
        )
        
        if not rule:
            return None
        
        return {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "condition": rule.condition,
            "action": rule.action.value,
            "priority": rule.priority,
            "enabled": rule.enabled
        }
    
    def get_statistics(self) -> dict[str, Any]:
        """获取策略统计信息
        
        Returns:
            dict: 统计信息
        """
        enabled_count = sum(1 for rule in self.policies if rule.enabled)
        disabled_count = len(self.policies) - enabled_count
        
        # 统计各动作类型的规则数量
        action_counts: dict[str, int] = {}
        for rule in self.policies:
            action_value = rule.action.value
            action_counts[action_value] = action_counts.get(action_value, 0) + 1
        
        return {
            "total_policies": len(self.policies),
            "enabled_count": enabled_count,
            "disabled_count": disabled_count,
            "action_distribution": action_counts
        }