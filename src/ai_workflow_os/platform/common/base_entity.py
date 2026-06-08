"""
基础实体类

定义所有领域实体的公共字段和行为，包括审计字段、乐观锁版本控制和多租户支持。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BaseEntity:
    """领域实体基类

    所有业务实体必须继承此类，提供统一的标识、审计和多租户字段。

    Attributes:
        id: 实体唯一标识
        created_at: 创建时间（UTC）
        updated_at: 最后更新时间（UTC）
        created_by: 创建者标识
        updated_by: 最后更新者标识
        tenant_id: 租户标识，用于多租户数据隔离
        version: 乐观锁版本号
        is_deleted: 软删除标记
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = field(default=None)
    updated_by: Optional[str] = field(default=None)
    tenant_id: Optional[str] = field(default=None)
    version: int = field(default=1)
    is_deleted: bool = field(default=False)

    def touch(self, operator: Optional[str] = None) -> None:
        """更新实体的修改时间和版本号

        Args:
            operator: 操作者标识
        """
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        if operator is not None:
            self.updated_by = operator

    def mark_deleted(self, operator: Optional[str] = None) -> None:
        """标记实体为已删除（软删除）

        Args:
            operator: 操作者标识
        """
        self.is_deleted = True
        self.touch(operator)

    def is_new(self) -> bool:
        """判断实体是否为新建（尚未持久化）

        Returns:
            是否为新建实体
        """
        return self.created_at == self.updated_at and self.version == 1
