"""
API模块 - 提供RESTful API接口

包含FastAPI应用、路由、中间件和数据模型定义。
"""

from .app import create_app

__all__ = ["create_app"]
