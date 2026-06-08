"""
工具定义实体

定义工具的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import ToolStatus, ToolType


@dataclass
class ToolDefinition(BaseEntity):
    """工具定义实体

    描述一个可复用工具的完整定义。

    Attributes:
        name: 工具名称
        description: 工具描述
        tool_type: 工具类型
        status: 工具状态
        endpoint: 工具端点（URL/函数路径等）
        parameters: 参数定义
        return_type: 返回类型定义
        authentication: 认证配置
        timeout: 超时时间（秒）
        retry_count: 重试次数
        usage_count: 使用次数
        author: 作者
        version: 当前版本号
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    tool_type: ToolType = ToolType.REST
    status: ToolStatus = ToolStatus.DRAFT
    endpoint: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    return_type: dict[str, Any] = field(default_factory=dict)
    authentication: dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    usage_count: int = 0
    author: str = ""
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def publish(self, operator: Optional[str] = None) -> None:
        """发布工具

        Args:
            operator: 操作者标识
        """
        self.status = ToolStatus.PUBLISHED
        self.touch(operator)

    def deprecate(self, operator: Optional[str] = None) -> None:
        """废弃工具

        Args:
            operator: 操作者标识
        """
        self.status = ToolStatus.DEPRECATED
        self.touch(operator)

    def increment_usage(self, operator: Optional[str] = None) -> None:
        """增加使用次数

        Args:
            operator: 操作者标识
        """
        self.usage_count += 1
        self.touch(operator)
