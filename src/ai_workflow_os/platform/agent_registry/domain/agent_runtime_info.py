"""
Agent运行时信息实体

定义Agent运行时的核心业务实体，包含实例信息、资源使用、请求统计和心跳状态。
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from ...common.base_entity import BaseEntity
from .enums import HealthStatus


@dataclass
class AgentRuntimeInfo(BaseEntity):
    """Agent运行时信息实体

    记录Agent运行时的实例信息，包括主机、端口、PID、运行时长、
    请求统计、错误计数和心跳状态等。

    Attributes:
        agent_registration_id: 关联的Agent注册标识
        instance_id: 运行实例唯一标识
        host: 实例主机地址
        port: 实例端口号
        pid: 进程ID（可选）
        uptime_seconds: 运行时长（秒）
        request_count: 累计请求数
        error_count: 累计错误数
        avg_latency_ms: 平均延迟（毫秒）
        last_heartbeat: 最近一次心跳时间（可选）
        status: 健康状态
    """

    agent_registration_id: str = ""
    instance_id: str = ""
    host: str = ""
    port: int = 0
    pid: int | None = None
    uptime_seconds: float = 0.0
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    last_heartbeat: datetime | None = field(default=None)
    status: HealthStatus = HealthStatus.UNKNOWN

    @property
    def error_rate(self) -> float:
        """计算错误率

        Returns:
            错误率（0.0 ~ 1.0），无请求时返回0.0
        """
        if self.request_count <= 0:
            return 0.0
        return self.error_count / self.request_count

    @property
    def is_responsive(self) -> bool:
        """判断实例是否响应正常（心跳在60秒内）

        Returns:
            是否响应正常
        """
        if self.last_heartbeat is None:
            return False
        now = datetime.now(UTC)
        return (now - self.last_heartbeat) <= timedelta(seconds=60)
