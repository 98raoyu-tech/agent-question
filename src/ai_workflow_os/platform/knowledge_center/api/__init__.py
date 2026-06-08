"""
知识中心 API层

提供知识源和文档相关的FastAPI路由。
"""

from .knowledge_governance_routes import router as knowledge_governance_router
from .knowledge_routes import router as knowledge_router
