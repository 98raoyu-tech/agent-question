"""
Prompt版本实体

管理Prompt模板的版本历史。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class PromptVersion(BaseEntity):
    """Prompt版本实体

    记录Prompt模板的版本快照。

    Attributes:
        template_id: 关联的模板标识
        version_number: 版本号
        content: 版本内容
        change_log: 变更日志
        is_current: 是否为当前版本
        metadata: 扩展元数据
    """

    template_id: str = ""
    version_number: str = ""
    content: str = ""
    change_log: str = ""
    is_current: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_as_current(self, operator: Optional[str] = None) -> None:
        """设置为当前版本

        Args:
            operator: 操作者标识
        """
        self.is_current = True
        self.touch(operator)

    def unset_current(self, operator: Optional[str] = None) -> None:
        """取消当前版本标记

        Args:
            operator: 操作者标识
        """
        self.is_current = False
        self.touch(operator)
