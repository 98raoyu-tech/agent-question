"""
Agent Ops 枚举定义

定义Agent运维管理相关的枚举类型，包括环境、部署策略、事故严重程度等。
"""

from enum import Enum


class Environment(str, Enum):
    """环境枚举"""

    DEV = "dev"
    """开发环境"""

    TEST = "test"
    """测试环境"""

    STAGING = "staging"
    """预发布环境"""

    PROD = "prod"
    """生产环境"""


class DeploymentStrategy(str, Enum):
    """部署策略枚举"""

    CANARY = "canary"
    """灰度发布"""

    BLUE_GREEN = "blue_green"
    """蓝绿部署"""

    ROLLING = "rolling"
    """滚动更新"""

    DIRECT = "direct"
    """直接发布"""


class DeploymentStatus(str, Enum):
    """部署状态枚举"""

    PENDING = "pending"
    """待部署"""

    DEPLOYING = "deploying"
    """部署中"""

    ACTIVE = "active"
    """已激活"""

    FAILED = "failed"
    """部署失败"""

    ROLLED_BACK = "rolled_back"
    """已回滚"""


class IncidentSeverity(str, Enum):
    """事故严重程度枚举"""

    LOW = "low"
    """低"""

    MEDIUM = "medium"
    """中"""

    HIGH = "high"
    """高"""

    CRITICAL = "critical"
    """严重"""


class IncidentStatus(str, Enum):
    """事故状态枚举"""

    OPEN = "open"
    """已打开"""

    INVESTIGATING = "investigating"
    """调查中"""

    MITIGATED = "mitigated"
    """已缓解"""

    RESOLVED = "resolved"
    """已解决"""

    CLOSED = "closed"
    """已关闭"""


class HealthStatus(str, Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    """健康"""

    DEGRADED = "degraded"
    """性能下降"""

    UNHEALTHY = "unhealthy"
    """不健康"""

    UNKNOWN = "unknown"
    """未知"""
