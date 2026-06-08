"""
工具注册表模块

管理所有已注册的MCP工具，提供工具定义、分类、搜索和验证功能。
采用单例模式确保全局唯一实例。
"""

from dataclasses import dataclass, field
from typing import Any, Callable
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """工具定义
    
    Attributes:
        name: 工具名称，作为唯一标识
        description: 工具功能描述
        handler: 工具处理函数
        input_schema: 输入参数的JSON Schema定义
        output_schema: 输出结果的JSON Schema定义
        category: 工具分类（如 "数据处理"、"文件操作" 等）
        version: 工具版本号
        permissions: 执行该工具所需的权限列表
    """
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    category: str = "未分类"
    version: str = "1.0.0"
    permissions: list[str] = field(default_factory=list)


class ToolRegistry:
    """工具注册表（单例模式）
    
    管理所有已注册的MCP工具，提供工具定义、分类、搜索和验证功能。
    
    Attributes:
        tools: 工具定义映射表，键为工具名称
    """
    
    _instance: "ToolRegistry | None" = None
    _initialized: bool = False
    
    def __new__(cls) -> "ToolRegistry":
        """单例模式：确保全局唯一实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化工具注册表（仅首次调用有效）"""
        if not ToolRegistry._initialized:
            self.tools: dict[str, ToolDefinition] = {}
            ToolRegistry._initialized = True
            logger.info("工具注册表已初始化")
    
    def register(self, tool_def: ToolDefinition) -> bool:
        """注册工具
        
        Args:
            tool_def: 工具定义对象
            
        Returns:
            bool: 注册成功返回True，工具名已存在返回False
        """
        # 检查工具名称是否已存在
        if tool_def.name in self.tools:
            logger.warning(f"工具 '{tool_def.name}' 已存在，注册失败")
            return False
        
        # 注册工具定义
        self.tools[tool_def.name] = tool_def
        logger.info(f"已注册工具: {tool_def.name} (分类: {tool_def.category})")
        return True
    
    def unregister(self, tool_name: str) -> bool:
        """注销工具
        
        Args:
            tool_name: 要注销的工具名称
            
        Returns:
            bool: 注销成功返回True，工具不存在返回False
        """
        if tool_name not in self.tools:
            logger.warning(f"工具 '{tool_name}' 不存在，注销失败")
            return False
        
        del self.tools[tool_name]
        logger.info(f"已注销工具: {tool_name}")
        return True
    
    def get(self, tool_name: str) -> ToolDefinition | None:
        """获取工具定义
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ToolDefinition: 工具定义对象，不存在返回None
        """
        return self.tools.get(tool_name)
    
    def list_by_category(self, category: str) -> list[ToolDefinition]:
        """按分类列出工具
        
        Args:
            category: 工具分类名称
            
        Returns:
            list: 该分类下的工具定义列表
        """
        return [
            tool_def for tool_def in self.tools.values()
            if tool_def.category == category
        ]
    
    def search(self, keyword: str) -> list[ToolDefinition]:
        """搜索工具
        
        根据关键词搜索工具名称和描述。
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            list: 匹配的工具定义列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for tool_def in self.tools.values():
            # 在名称和描述中搜索关键词
            if (keyword_lower in tool_def.name.lower() or 
                keyword_lower in tool_def.description.lower()):
                results.append(tool_def)
        
        return results
    
    def validate_input(self, tool_name: str, input_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """验证输入数据
        
        根据工具的输入Schema验证输入数据。
        
        Args:
            tool_name: 工具名称
            input_data: 待验证的输入数据
            
        Returns:
            tuple: (验证是否通过, 错误信息列表)
        """
        # 获取工具定义
        tool_def = self.tools.get(tool_name)
        if not tool_def:
            return False, [f"工具 '{tool_name}' 不存在"]
        
        # 如果没有定义输入Schema，则跳过验证
        if not tool_def.input_schema:
            return True, []
        
        errors = []
        schema = tool_def.input_schema
        
        # 检查必需字段
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            if field_name not in input_data:
                errors.append(f"缺少必需字段: {field_name}")
        
        # 检查字段类型（简单验证）
        properties = schema.get("properties", {})
        for field_name, field_value in input_data.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type:
                    # 类型映射
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict
                    }
                    
                    expected_python_type = type_map.get(expected_type)
                    if expected_python_type and not isinstance(field_value, expected_python_type):
                        errors.append(f"字段 '{field_name}' 类型错误，期望 {expected_type}")
        
        return len(errors) == 0, errors
    
    def get_all_schemas(self) -> dict[str, Any]:
        """获取所有工具的Schema
        
        用于LLM function calling，返回所有工具的输入Schema格式。
        
        Returns:
            dict: 所有工具的Schema映射表
        """
        schemas = {}
        
        for tool_name, tool_def in self.tools.items():
            schemas[tool_name] = {
                "name": tool_name,
                "description": tool_def.description,
                "parameters": tool_def.input_schema
            }
        
        return schemas
    
    def get_categories(self) -> list[str]:
        """获取所有工具分类
        
        Returns:
            list: 分类名称列表
        """
        categories = set()
        for tool_def in self.tools.values():
            categories.add(tool_def.category)
        return sorted(list(categories))
    
    def get_statistics(self) -> dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            dict: 统计信息，包括工具总数、分类统计等
        """
        category_counts: dict[str, int] = {}
        for tool_def in self.tools.values():
            category_counts[tool_def.category] = category_counts.get(tool_def.category, 0) + 1
        
        return {
            "total_tools": len(self.tools),
            "categories": category_counts,
            "category_count": len(category_counts)
        }