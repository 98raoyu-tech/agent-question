"""
熔断器模块

实现熔断器模式（Circuit Breaker Pattern），防止级联故障。
支持三种状态：
- CLOSED: 正常状态，允许请求通过
- OPEN: 熔断状态，拒绝所有请求
- HALF_OPEN: 半开状态，允许少量请求探测服务是否恢复
"""

import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Awaitable

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class CircuitState(str, Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# ==================== 异常定义 ====================

class CircuitBreakerOpenError(Exception):
    """熔断器打开异常

    当熔断器处于 OPEN 状态时，调用被保护的函数会抛出此异常。
    """

    def __init__(self, breaker_name: str, retry_after: float) -> None:
        """初始化异常

        Args:
            breaker_name: 熔断器名称
            retry_after: 建议重试等待时间（秒）
        """
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"熔断器 '{breaker_name}' 已打开，请在 {retry_after:.1f} 秒后重试"
        )


# ==================== 熔断器核心类 ====================

class CircuitBreaker:
    """熔断器

    实现熔断器模式，防止级联故障。当失败次数超过阈值时，
    熔断器打开并拒绝所有请求，经过恢复超时后进入半开状态，
    允许少量请求探测服务是否恢复。

    Attributes:
        name: 熔断器名称
        failure_threshold: 失败次数阈值
        recovery_timeout: 恢复超时时间（秒）
        state: 当前状态
        failure_count: 连续失败次数
        last_failure_time: 最后一次失败时间
        success_count: 半开状态下的成功次数
        half_open_max_calls: 半开状态最大允许调用数
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ) -> None:
        """初始化熔断器

        Args:
            name: 熔断器名称
            failure_threshold: 触发熔断的连续失败次数阈值
            recovery_timeout: 从 OPEN 到 HALF_OPEN 的恢复超时时间（秒）
            half_open_max_calls: 半开状态下的最大探测调用数
        """
        self.name: str = name
        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: float = recovery_timeout
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self.success_count: int = 0
        self.half_open_max_calls: int = half_open_max_calls
        self._half_open_calls: int = 0
        logger.info(
            "熔断器 '%s' 已初始化 (阈值: %d, 恢复超时: %.1fs)",
            name,
            failure_threshold,
            recovery_timeout,
        )

    # ==================== 核心调用方法 ====================

    async def call(
        self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """通过熔断器调用异步函数

        根据熔断器状态决定是否允许调用。

        Args:
            func: 待调用的异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            CircuitBreakerOpenError: 当熔断器处于 OPEN 状态时抛出
        """
        # 检查是否可以执行
        if not self._can_execute():
            retry_after = self._get_retry_after()
            raise CircuitBreakerOpenError(self.name, retry_after)

        try:
            # 执行函数调用
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as error:
            self._on_failure()
            raise

    # ==================== 状态管理 ====================

    def _can_execute(self) -> bool:
        """判断是否可以执行调用

        Returns:
            bool: 允许执行返回 True，否则返回 False
        """
        # CLOSED 状态：允许所有调用
        if self.state == CircuitState.CLOSED:
            return True

        # OPEN 状态：检查是否应该转入 HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False

        # HALF_OPEN 状态：限制调用数量
        if self.state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls

        return False

    def _on_success(self) -> None:
        """成功回调"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self._half_open_calls += 1

            # 半开状态下连续成功足够多，重置熔断器
            if self.success_count >= self.half_open_max_calls:
                self.reset()
                logger.info("熔断器 '%s' 已恢复正常 (CLOSED)", self.name)
        else:
            # CLOSED 状态下重置失败计数
            self.failure_count = 0

    def _on_failure(self) -> None:
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # 半开状态下失败，立即打开熔断器
            self._transition_to_open()
            logger.warning(
                "熔断器 '%s' 半开状态下失败，重新打开 (OPEN)", self.name
            )
        elif self.failure_count >= self.failure_threshold:
            # CLOSED 状态下失败次数超过阈值，打开熔断器
            self._transition_to_open()
            logger.warning(
                "熔断器 '%s' 失败次数达到阈值 %d，已打开 (OPEN)",
                self.name,
                self.failure_threshold,
            )

    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置

        Returns:
            bool: 超过恢复超时时间返回 True
        """
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _get_retry_after(self) -> float:
        """获取建议重试等待时间

        Returns:
            float: 建议等待时间（秒）
        """
        elapsed = time.time() - self.last_failure_time
        return max(0.0, self.recovery_timeout - elapsed)

    # ==================== 状态转换 ====================

    def _transition_to_open(self) -> None:
        """转换到 OPEN 状态"""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()

    def _transition_to_half_open(self) -> None:
        """转换到 HALF_OPEN 状态"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self._half_open_calls = 0

    def reset(self) -> None:
        """重置熔断器到 CLOSED 状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self._half_open_calls = 0
        self.last_failure_time = 0.0
        logger.info("熔断器 '%s' 已重置", self.name)

    # ==================== 状态查询 ====================

    def get_state(self) -> dict[str, Any]:
        """获取熔断器状态

        Returns:
            dict: 熔断器状态信息
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "success_count": self.success_count,
            "retry_after": self._get_retry_after() if self.state == CircuitState.OPEN else 0.0,
        }


# ==================== 装饰器 ====================

def circuit_breaker(
    threshold: int = 5,
    timeout: float = 60.0,
    name: str = "",
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """熔断器装饰器

    便捷地为异步函数添加熔断器保护。

    Args:
        threshold: 失败次数阈值
        timeout: 恢复超时时间（秒）
        name: 熔断器名称，默认使用函数名

    Returns:
        装饰器函数

    Usage:
        @circuit_breaker(threshold=3, timeout=30.0)
        async def call_api():
            ...
    """
    # 使用函数名作为默认熔断器名称
    breaker = CircuitBreaker(
        name=name or "decorated",
        failure_threshold=threshold,
        recovery_timeout=timeout,
    )

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await breaker.call(func, *args, **kwargs)

        # 暴露熔断器实例供外部访问
        wrapper.circuit_breaker = breaker  # type: ignore[attr-defined]
        return wrapper

    return decorator
