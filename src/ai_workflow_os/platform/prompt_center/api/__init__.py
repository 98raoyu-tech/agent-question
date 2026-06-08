"""
Prompt中心 API层

提供Prompt模板相关的FastAPI路由。
"""

from .prompt_lifecycle_routes import router as prompt_lifecycle_router
from .prompt_routes import router as prompt_router
