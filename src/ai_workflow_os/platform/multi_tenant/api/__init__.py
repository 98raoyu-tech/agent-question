"""
多租户API层

提供租户、组织、项目、环境和RBAC相关的FastAPI路由。
"""

from .multi_tenant_routes import router as multi_tenant_router
