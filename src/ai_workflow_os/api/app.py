"""
FastAPI应用入口

创建和配置FastAPI应用实例，注册路由、中间件和异常处理器。
支持前后端分离部署，通过环境变量配置CORS。
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..platform.adapters.api import adapter_router
from ..platform.agent_lifecycle.api import agent_lifecycle_router
from ..platform.agent_ops.api import agent_ops_router
from ..platform.agent_pipeline.api import pipeline_router
from ..platform.agent_registry.api import agent_registry_router
from ..platform.agent_studio.api import agent_studio_router
from ..platform.cost_center.api import cost_analytics_router, cost_router
from ..platform.evaluation_center.api import evaluation_router
from ..platform.evaluation_gate.api import evaluation_gate_router
from ..platform.event_center.api import event_center_router
from ..platform.governance.api import governance_engine_router, governance_router
from ..platform.knowledge_center.api import knowledge_governance_router, knowledge_router
from ..platform.multi_agent_org.api import multi_agent_org_router
from ..platform.multi_tenant.api import multi_tenant_router
from ..platform.prompt_center.api import prompt_lifecycle_router, prompt_router
from ..platform.tool_marketplace.api import tool_lifecycle_router, tool_marketplace_router
from ..platform.workflow_engine.api import workflow_engine_router
from .middleware.rate_limit import RateLimitMiddleware
from .routes import (
    agent_router,
    approval_router,
    auth_router,
    memory_router,
    tool_router,
    workflow_router,
)
from .schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理器

    在应用启动时初始化必要的服务，在关闭时优雅退出。

    Args:
        app: FastAPI应用实例

    Yields:
        None
    """
    # ==================== 启动阶段 ====================
    logger.info("正在启动 Enterprise Agent Platform...")

    # TODO: 初始化HarnessRuntime
    # app.state.harness = HarnessRuntime()
    # await app.state.harness.initialize()

    # TODO: 初始化Memory服务
    # app.state.memory = MemoryService()
    # await app.state.memory.connect()

    # TODO: 初始化EventBus
    # app.state.event_bus = EventBus()
    # await app.state.event_bus.start()

    logger.info("Enterprise Agent Platform 启动完成")

    yield

    # ==================== 关闭阶段 ====================
    logger.info("正在关闭 Enterprise Agent Platform...")

    # TODO: 优雅关闭EventBus
    # if hasattr(app.state, 'event_bus'):
    #     await app.state.event_bus.stop()

    # TODO: 关闭Memory服务
    # if hasattr(app.state, 'memory'):
    #     await app.state.memory.disconnect()

    # TODO: 关闭HarnessRuntime
    # if hasattr(app.state, 'harness'):
    #     await app.state.harness.shutdown()

    logger.info("Enterprise Agent Platform 已关闭")


def create_app(
    title: str = "Enterprise Agent Platform",
    version: str = "2.0.0",
    debug: bool = False,
) -> FastAPI:
    """创建FastAPI应用实例

    Args:
        title: 应用标题
        version: 应用版本
        debug: 是否开启调试模式

    Returns:
        配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="Enterprise Agent Platform",
        version="2.0.0",
        description="企业级Agent中台 - 提供Agent生命周期管理、评估门禁、AgentOps、多租户隔离、知识治理、工具生命周期、Prompt生命周期、事件驱动架构、成本中心、治理引擎、多Agent协作等完整企业级能力",
        lifespan=lifespan,
        debug=debug,
    )

    # ==================== 注册中间件 ====================

    # CORS中间件 - 支持前后端分离部署
    # 通过环境变量 CORS_ORIGINS 配置允许的源，多个用逗号分隔
    # 例如: CORS_ORIGINS=http://localhost:3000,https://example.com
    cors_origins_str = os.getenv("CORS_ORIGINS", "*")
    cors_origins = (
        [origin.strip() for origin in cors_origins_str.split(",")]
        if cors_origins_str != "*"
        else ["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求日志中间件
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """记录请求日志"""
        import time

        start_time = time.time()

        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        duration = time.time() - start_time

        # 记录响应信息
        logger.info(
            f"请求完成: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
            },
        )

        # 添加处理时间响应头
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response

    # 限流中间件
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=100,
        window_seconds=60,
    )

    # ==================== 注册路由 ====================

    # 原有路由
    app.include_router(auth_router)
    app.include_router(workflow_router)
    app.include_router(agent_router)
    app.include_router(memory_router)
    app.include_router(tool_router)
    app.include_router(approval_router)

    # 企业级平台模块路由
    app.include_router(agent_studio_router)
    app.include_router(agent_lifecycle_router)
    app.include_router(agent_ops_router)
    app.include_router(knowledge_router)
    app.include_router(knowledge_governance_router)
    app.include_router(evaluation_router)
    app.include_router(evaluation_gate_router)
    app.include_router(prompt_router)
    app.include_router(prompt_lifecycle_router)
    app.include_router(cost_router)
    app.include_router(cost_analytics_router)
    app.include_router(governance_router)
    app.include_router(governance_engine_router)
    app.include_router(tool_marketplace_router)
    app.include_router(tool_lifecycle_router)
    app.include_router(multi_tenant_router)
    app.include_router(event_center_router)
    app.include_router(multi_agent_org_router)

    # VNext 企业级闭环路由
    app.include_router(pipeline_router)
    app.include_router(agent_registry_router)
    app.include_router(adapter_router)
    app.include_router(workflow_engine_router)

    # ==================== 注册异常处理器 ====================

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """全局异常处理器

        捕获所有未处理的异常，返回统一的错误响应格式。

        Args:
            request: FastAPI请求对象
            exc: 异常对象

        Returns:
            统一格式的错误响应
        """
        logger.error(
            f"未处理的异常: {str(exc)}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "error_type": type(exc).__name__,
            },
        )

        error_response = ErrorResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="服务器内部错误",
            detail=str(exc) if debug else None,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )

    # ==================== 注册健康检查端点 ====================

    @app.get(
        "/health",
        summary="健康检查",
        description="检查服务健康状态",
        tags=["系统"],
    )
    async def health_check() -> dict:
        """健康检查端点

        Returns:
            包含服务状态的字典
        """
        return {
            "status": "healthy",
            "version": version,
            "service": title,
        }

    return app


# 创建默认应用实例
app = create_app()
