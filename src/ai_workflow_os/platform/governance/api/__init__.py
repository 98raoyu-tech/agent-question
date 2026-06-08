"""
治理中心 API层

提供治理相关的FastAPI路由。
"""

from .governance_engine_routes import router as governance_engine_router
from .governance_routes import router as governance_router
