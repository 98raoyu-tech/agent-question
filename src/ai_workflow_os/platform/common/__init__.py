"""
共享基础设施模块

提供基础实体、DTO、领域事件、仓储抽象、分页查询和平台级异常等通用组件。
"""

from .base_dto import BaseDTO
from .base_entity import BaseEntity
from .base_event import BaseEvent
from .base_repository import BaseRepository
from .exceptions import (
    BusinessRuleViolationException,
    ConcurrencyConflictException,
    DuplicateResourceException,
    PlatformException,
    ResourceNotFoundException,
    TenantAccessException,
    ValidationException,
)
from .pagination import PaginatedRequest, PaginatedResponse

__all__ = [
    "BaseEntity",
    "BaseDTO",
    "BaseEvent",
    "BaseRepository",
    "PaginatedRequest",
    "PaginatedResponse",
    "PlatformException",
    "ResourceNotFoundException",
    "DuplicateResourceException",
    "ValidationException",
    "BusinessRuleViolationException",
    "ConcurrencyConflictException",
    "TenantAccessException",
]
