"""
工具版本实体

管理工具的版本历史。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class ToolVersion(BaseEntity):
    """工具版本实体

    记录工具定义的版本快照。

    Attributes:
        tool_id: 关联的工具标识
        version_number: 版本号
        change_log: 变更日志
        snapshot: 工具定义快照数据
        is_current: 是否为当前版本
    """

    tool_id: str = ""
    version_number: str = ""
    change_log: str = ""
    snapshot: dict[str, Any] = field(default_factory=dict)
    is_current: bool = False

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
