"""
MCP工具路由模块

负责MCP（Model Context Protocol）工具的统一路由和执行。
提供工具注册、中间件链、权限检查和请求路由功能。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import asyncio
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class ToolRoute:
    """工具路由定义
    
    Attributes:
        tool_name: 工具名称，作为唯一标识
        handler: 工具处理函数，支持同步和异步调用
        description: 工具功能描述
        schema: 工具输入输出的JSON Schema定义
        required_permissions: 执行该工具所需的权限列表
    """
    tool_name: str
    handler: Callable[..., Any]
    description: str
    schema: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)


class MCPRouter:
    """MCP工具路由器
    
    负责MCP工具的统一路由，支持中间件链、权限检查和异步执行。
    
    Attributes:
        routes: 工具路由映射表，键为工具名称
        middleware: 中间件函数列表，按注册顺序执行
    """
    
    def __init__(self) -> None:
        """初始化MCP路由器"""
        self.routes: dict[str, ToolRoute] = {}
        self.middleware: list[Callable[..., Awaitable[dict[str, Any]]]] = []
    
    def register_route(
        self,
        tool_name: str,
        handler: Callable[..., Any],
        schema: dict[str, Any] | None = None,
        permissions: list[str] | None = None,
        description: str = ""
    ) -> None:
        """注册工具路由
        
        Args:
            tool_name: 工具名称，必须唯一
            handler: 工具处理函数
            schema: 工具的输入输出Schema定义
            permissions: 执行工具所需的权限列表
            description: 工具功能描述
        """
        # 检查工具名称是否已存在
        if tool_name in self.routes:
            logger.warning(f"工具路由 '{tool_name}' 已存在，将被覆盖")
        
        # 创建工具路由定义
        route = ToolRoute(
            tool_name=tool_name,
            handler=handler,
            description=description,
            schema=schema or {},
            required_permissions=permissions or []
        )
        
        self.routes[tool_name] = route
        logger.info(f"已注册工具路由: {tool_name}")
    
    def unregister_route(self, tool_name: str) -> bool:
        """注销工具路由
        
        Args:
            tool_name: 要注销的工具名称
            
        Returns:
            bool: 注销成功返回True，工具不存在返回False
        """
        if tool_name not in self.routes:
            logger.warning(f"工具路由 '{tool_name}' 不存在")
            return False
        
        del self.routes[tool_name]
        logger.info(f"已注销工具路由: {tool_name}")
        return True
    
    async def route_request(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """路由请求到对应工具
        
        Args:
            tool_name: 目标工具名称
            params: 工具执行参数
            context: 请求上下文信息（如用户ID、权限等）
            
        Returns:
            dict: 工具执行结果
            
        Raises:
            ValueError: 工具不存在时抛出
            PermissionError: 权限不足时抛出
        """
        # 检查工具是否存在
        if tool_name not in self.routes:
            raise ValueError(f"工具 '{tool_name}' 不存在")
        
        route = self.routes[tool_name]
        context = context or {}
        
        # 执行中间件链
        middleware_result = await self._execute_middleware_chain(
            tool_name, params, context
        )
        
        # 检查中间件是否阻止执行
        if middleware_result.get("blocked", False):
            return {
                "success": False,
                "error": middleware_result.get("reason", "中间件阻止执行"),
                "tool_name": tool_name
            }
        
        # 执行工具处理函数
        try:
            # 检查是否为异步函数
            if asyncio.iscoroutinefunction(route.handler):
                result = await route.handler(params, context)
            else:
                result = route.handler(params, context)
            
            logger.info(f"工具 '{tool_name}' 执行成功")
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name
            }
        except Exception as e:
            logger.error(f"工具 '{tool_name}' 执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    def add_middleware(self, middleware_func: Callable[..., Awaitable[dict[str, Any]]]) -> None:
        """添加中间件
        
        中间件函数签名: async def middleware(tool_name, params, context) -> dict
        返回字典中可包含 "blocked": True 来阻止执行
        
        Args:
            middleware_func: 中间件函数
        """
        self.middleware.append(middleware_func)
        logger.info(f"已添加中间件: {middleware_func.__name__}")
    
    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有可用工具
        
        Returns:
            list: 工具信息列表，包含名称、描述、Schema等
        """
        tools = []
        for tool_name, route in self.routes.items():
            tools.append({
                "tool_name": tool_name,
                "description": route.description,
                "schema": route.schema,
                "required_permissions": route.required_permissions
            })
        return tools
    
    def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """获取工具的输入输出Schema
        
        Args:
            tool_name: 工具名称
            
        Returns:
            dict: 工具的Schema定义
            
        Raises:
            ValueError: 工具不存在时抛出
        """
        if tool_name not in self.routes:
            raise ValueError(f"工具 '{tool_name}' 不存在")
        
        return self.routes[tool_name].schema
    
    async def _execute_middleware_chain(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行中间件链
        
        按注册顺序执行所有中间件，任何中间件返回 blocked=True 都会阻止执行。
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 请求上下文
            
        Returns:
            dict: 中间件执行结果，包含是否被阻止及原因
        """
        result = {"blocked": False, "reason": ""}
        
        # 按顺序执行中间件
        for middleware in self.middleware:
            try:
                middleware_result = await middleware(tool_name, params, context)
                
                # 检查中间件是否阻止执行
                if middleware_result.get("blocked", False):
                    result["blocked"] = True
                    result["reason"] = middleware_result.get("reason", "中间件阻止执行")
                    logger.warning(f"中间件 {middleware.__name__} 阻止工具 '{tool_name}' 执行")
                    break
                    
                # 合并中间件修改的上下文
                if "context" in middleware_result:
                    context.update(middleware_result["context"])
                    
            except Exception as e:
                logger.error(f"中间件 {middleware.__name__} 执行异常: {str(e)}")
                result["blocked"] = True
                result["reason"] = f"中间件执行异常: {str(e)}"
                break
        
        return result