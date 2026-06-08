"""
工具路由

提供MCP工具的查询、详情和调用功能。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/tools", tags=["工具"])


# ==================== 请求/响应模型 ====================

class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(description="参数名")
    type: str = Field(description="参数类型")
    description: str = Field(description="参数描述")
    required: bool = Field(default=False, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")


class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    category: str = Field(description="工具分类")
    version: str = Field(default="1.0.0", description="工具版本")
    parameters: list[ToolParameter] = Field(default_factory=list, description="参数列表")
    enabled: bool = Field(default=True, description="是否启用")


class ToolInvokeRequest(BaseModel):
    """工具调用请求"""
    parameters: dict = Field(default_factory=dict, description="调用参数")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")


class ToolInvokeResponse(BaseModel):
    """工具调用响应"""
    tool_name: str = Field(description="工具名称")
    success: bool = Field(description="是否成功")
    result: Optional[Any] = Field(description="调用结果")
    error: Optional[str] = Field(description="错误信息")
    duration_ms: float = Field(description="执行耗时（毫秒）")


class ToolCategory(BaseModel):
    """工具分类"""
    name: str = Field(description="分类名称")
    description: str = Field(description="分类描述")
    tool_count: int = Field(description="工具数量")


# ==================== 模拟数据存储 ====================
# TODO: 替换为实际的MCP工具注册中心

_tool_registry: dict[str, ToolInfo] = {
    "web_search": ToolInfo(
        name="web_search",
        description="网页搜索工具，支持多种搜索引擎",
        category="搜索",
        parameters=[
            ToolParameter(name="query", type="string", description="搜索关键词", required=True),
            ToolParameter(name="max_results", type="integer", description="最大结果数", default=10),
        ],
    ),
    "code_execute": ToolInfo(
        name="code_execute",
        description="代码执行工具，支持Python、JavaScript等语言",
        category="编程",
        parameters=[
            ToolParameter(name="language", type="string", description="编程语言", required=True),
            ToolParameter(name="code", type="string", description="要执行的代码", required=True),
        ],
    ),
    "file_read": ToolInfo(
        name="file_read",
        description="文件读取工具",
        category="文件",
        parameters=[
            ToolParameter(name="path", type="string", description="文件路径", required=True),
            ToolParameter(name="encoding", type="string", description="文件编码", default="utf-8"),
        ],
    ),
    "database_query": ToolInfo(
        name="database_query",
        description="数据库查询工具",
        category="数据",
        parameters=[
            ToolParameter(name="connection", type="string", description="连接字符串", required=True),
            ToolParameter(name="query", type="string", description="SQL查询语句", required=True),
        ],
    ),
}


# ==================== 路由处理函数 ====================

@router.get(
    "/tools",
    summary="列出工具",
    description="获取所有可用的MCP工具列表",
)
async def list_tools(
    category: Optional[str] = Query(default=None, description="分类过滤"),
    enabled_only: bool = Query(default=True, description="仅显示启用的工具"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """列出所有MCP工具

    Args:
        category: 分类过滤条件
        enabled_only: 是否仅显示启用的工具
        current_user: 当前认证用户

    Returns:
        工具列表
    """
    tools = list(_tool_registry.values())

    # 应用过滤条件
    if enabled_only:
        tools = [t for t in tools if t.enabled]
    if category:
        tools = [t for t in tools if t.category == category]

    return {
        "items": [t.model_dump() for t in tools],
        "total": len(tools),
    }


@router.get(
    "/tools/categories",
    summary="获取工具分类",
    description="获取所有工具分类及其工具数量",
)
async def get_tool_categories(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取工具分类

    Args:
        current_user: 当前认证用户

    Returns:
        分类列表
    """
    # 统计每个分类的工具数量
    category_map: dict[str, list[ToolInfo]] = {}
    for tool in _tool_registry.values():
        if tool.category not in category_map:
            category_map[tool.category] = []
        category_map[tool.category].append(tool)

    categories = [
        ToolCategory(
            name=cat_name,
            description=f"{cat_name}相关工具",
            tool_count=len(cat_tools),
        )
        for cat_name, cat_tools in category_map.items()
    ]

    return {
        "items": [c.model_dump() for c in categories],
        "total": len(categories),
    }


@router.get(
    "/tools/{tool_name}",
    response_model=ToolInfo,
    summary="获取工具详情",
    description="根据工具名称获取工具详情和schema",
)
async def get_tool(
    tool_name: str,
    current_user: dict = Depends(get_current_user),
) -> ToolInfo:
    """获取工具详情

    Args:
        tool_name: 工具名称
        current_user: 当前认证用户

    Returns:
        工具详细信息

    Raises:
        HTTPException: 工具不存在
    """
    tool = _tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工具不存在: {tool_name}",
        )
    return tool


@router.post(
    "/tools/{tool_name}/invoke",
    response_model=ToolInvokeResponse,
    summary="调用工具",
    description="调用指定的MCP工具",
)
async def invoke_tool(
    tool_name: str,
    request: ToolInvokeRequest,
    current_user: dict = Depends(get_current_user),
) -> ToolInvokeResponse:
    """调用工具

    Args:
        tool_name: 工具名称
        request: 工具调用请求
        current_user: 当前认证用户

    Returns:
        工具调用结果

    Raises:
        HTTPException: 工具不存在或已禁用
    """
    import time

    # 检查工具是否存在
    tool = _tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工具不存在: {tool_name}",
        )

    # 检查工具是否启用
    if not tool.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工具已禁用: {tool_name}",
        )

    # 验证必需参数
    required_params = {p.name for p in tool.parameters if p.required}
    provided_params = set(request.parameters.keys())
    missing_params = required_params - provided_params
    if missing_params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"缺少必需参数: {', '.join(missing_params)}",
        )

    # 模拟工具执行
    start_time = time.time()
    # TODO: 替换为实际的MCP工具调用
    result = {
        "message": f"工具 {tool_name} 执行成功",
        "parameters": request.parameters,
    }
    duration_ms = (time.time() - start_time) * 1000

    return ToolInvokeResponse(
        tool_name=tool_name,
        success=True,
        result=result,
        error=None,
        duration_ms=round(duration_ms, 2),
    )
