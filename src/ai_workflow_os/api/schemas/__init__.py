"""
Schema模块 - Pydantic数据模型定义

包含通用响应模型和各业务模块的请求/响应模型。
"""

from .common import APIResponse, PaginatedResponse, ErrorResponse

__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
