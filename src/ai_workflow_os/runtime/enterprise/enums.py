"""
企业级运行时枚举定义

定义检查点状态、快照类型、故障转移状态和工作节点健康状态等枚举。
"""

from enum import Enum


class CheckpointStatus(str, Enum):
    """检查点状态枚举"""

    CREATED = "created"
    """已创建"""

    SAVED = "saved"
    """已保存"""

    RESTORED = "restored"
    """已恢复"""

    EXPIRED = "expired"
    """已过期"""


class SnapshotType(str, Enum):
    """快照类型枚举"""

    FULL = "full"
    """全量快照"""

    INCREMENTAL = "incremental"
    """增量快照"""

    DELTA = "delta"
    """差异快照"""


class FailoverState(str, Enum):
    """故障转移状态枚举"""

    PRIMARY = "primary"
    """主节点"""

    SECONDARY = "secondary"
    """备用节点"""

    FAILOVER = "failover"
    """故障转移中"""

    RECOVERED = "recovered"
    """已恢复"""


class WorkerHealthStatus(str, Enum):
    """工作节点健康状态枚举"""

    HEALTHY = "healthy"
    """健康"""

    UNHEALTHY = "unhealthy"
    """不健康"""

    DEGRADED = "degraded"
    """降级"""

    DEAD = "dead"
    """死亡"""
