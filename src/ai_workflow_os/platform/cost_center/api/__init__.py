"""
成本中心 API层

提供成本相关的FastAPI路由。
"""

from .cost_analytics_routes import router as cost_analytics_router
from .cost_routes import router as cost_router
