"""
Prompt模板实体

定义Prompt模板的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import PromptCategory, PromptStatus


@dataclass
class PromptTemplate(BaseEntity):
    """Prompt模板实体

    管理Prompt模板的完整生命周期。

    Attributes:
        name: 模板名称
        description: 模板描述
        content: 模板内容
        category: 模板分类
        status: 模板状态
        variables: 变量定义列表
        model_compatibility: 兼容的模型列表
        usage_count: 使用次数
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    content: str = ""
    category: PromptCategory = PromptCategory.TEMPLATE
    status: PromptStatus = PromptStatus.DRAFT
    variables: list[dict[str, Any]] = field(default_factory=list)
    model_compatibility: list[str] = field(default_factory=list)
    usage_count: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def activate(self, operator: Optional[str] = None) -> None:
        """激活模板

        Args:
            operator: 操作者标识
        """
        self.status = PromptStatus.ACTIVE
        self.touch(operator)

    def archive(self, operator: Optional[str] = None) -> None:
        """归档模板

        Args:
            operator: 操作者标识
        """
        self.status = PromptStatus.ARCHIVED
        self.touch(operator)

    def increment_usage(self, operator: Optional[str] = None) -> None:
        """增加使用次数

        Args:
            operator: 操作者标识
        """
        self.usage_count += 1
        self.touch(operator)

    def render(self, variables: dict[str, str]) -> str:
        """渲染模板

        Args:
            variables: 变量值字典

        Returns:
            渲染后的内容
        """
        rendered = self.content
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return rendered
