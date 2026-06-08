"""
限流中间件

基于Redis的滑动窗口限流算法，防止API被滥用。
"""

import time
from typing import Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于Redis的滑动窗口限流中间件"""

    def __init__(
        self,
        app,
        redis_client: Optional[object] = None,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """初始化限流中间件

        Args:
            app: FastAPI应用实例
            redis_client: Redis客户端实例，为None时使用内存存储
            max_requests: 窗口期内最大请求数
            window_seconds: 滑动窗口时间（秒）
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # 内存存储（当Redis不可用时使用）
        self._memory_store: dict[str, list[float]] = {}

    def _get_client_id(self, request: Request) -> str:
        """获取客户端唯一标识

        优先使用X-Forwarded-For头，其次使用客户端IP。

        Args:
            request: FastAPI请求对象

        Returns:
            客户端标识字符串
        """
        # 从代理头获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一个IP（最初的客户端IP）
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # 使用直接连接的客户端IP
            client_ip = request.client.host if request.client else "unknown"

        # 组合用户标识（如果有认证信息）
        user_id = request.headers.get("X-User-ID", "")
        if user_id:
            return f"user:{user_id}"

        return f"ip:{client_ip}"

    async def _is_rate_limited(self, client_id: str) -> bool:
        """检查客户端是否被限流

        使用滑动窗口算法，检查指定时间窗口内的请求数量。

        Args:
            client_id: 客户端标识

        Returns:
            True表示被限流，False表示未被限流
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds

        if self.redis_client:
            return await self._check_rate_limit_redis(client_id, current_time, window_start)

        return self._check_rate_limit_memory(client_id, current_time, window_start)

    async def _check_rate_limit_redis(
        self,
        client_id: str,
        current_time: float,
        window_start: float,
    ) -> bool:
        """使用Redis检查限流

        Args:
            client_id: 客户端标识
            current_time: 当前时间戳
            window_start: 窗口开始时间戳

        Returns:
            True表示被限流
        """
        key = f"rate_limit:{client_id}"

        try:
            # 使用Redis事务执行滑动窗口操作
            pipe = self.redis_client.pipeline()

            # 移除窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 统计当前窗口内的请求数
            pipe.zcard(key)

            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})

            # 设置key过期时间
            pipe.expire(key, self.window_seconds)

            results = await pipe.execute()
            request_count = results[1]

            return request_count >= self.max_requests

        except Exception:
            # Redis异常时降级到不限流
            return False

    def _check_rate_limit_memory(
        self,
        client_id: str,
        current_time: float,
        window_start: float,
    ) -> bool:
        """使用内存检查限流

        Args:
            client_id: 客户端标识
            current_time: 当前时间戳
            window_start: 窗口开始时间戳

        Returns:
            True表示被限流
        """
        # 获取或初始化客户端请求记录
        if client_id not in self._memory_store:
            self._memory_store[client_id] = []

        timestamps = self._memory_store[client_id]

        # 移除窗口外的旧记录
        self._memory_store[client_id] = [
            ts for ts in timestamps if ts > window_start
        ]

        # 检查是否超过限制
        if len(self._memory_store[client_id]) >= self.max_requests:
            return True

        # 记录当前请求
        self._memory_store[client_id].append(current_time)
        return False

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """中间件处理入口

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP响应对象
        """
        # 健康检查端点不限流
        if request.url.path == "/health":
            return await call_next(request)

        # 获取客户端标识
        client_id = self._get_client_id(request)

        # 检查是否被限流
        if await self._is_rate_limited(client_id):
            return Response(
                content='{"code": 429, "message": "请求过于频繁，请稍后再试"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流相关响应头
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)

        return response
