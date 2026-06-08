"""
企业级故障转移管理器

提供工作节点故障检测、故障转移执行、恢复和故障历史查询功能。
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from ...platform.common.base_entity import BaseEntity
from .checkpoint_manager import CheckpointManager
from .enums import FailoverState, WorkerHealthStatus
from .heartbeat_manager import HeartbeatManager, WorkerInfo

logger = logging.getLogger(__name__)


@dataclass
class FailoverRecord(BaseEntity):
    """故障转移记录实体

    记录故障转移事件的完整信息，包括源状态、目标状态和原因。

    Attributes:
        worker_id: 关联的工作节点标识
        from_state: 转移前状态
        to_state: 转移后状态
        reason: 转移原因
        completed_at: 完成时间
    """

    worker_id: str = ""
    from_state: FailoverState = FailoverState.PRIMARY
    to_state: FailoverState = FailoverState.FAILOVER
    reason: str = ""
    completed_at: datetime | None = None


class FailoverManager:
    """故障转移管理器

    协调心跳管理和检查点管理，实现故障检测、故障转移执行和恢复的完整流程。
    """

    def __init__(
        self,
        heartbeat_manager: HeartbeatManager,
        checkpoint_manager: CheckpointManager,
    ) -> None:
        """初始化故障转移管理器

        Args:
            heartbeat_manager: 心跳管理器实例
            checkpoint_manager: 检查点管理器实例
        """
        self.heartbeat_manager = heartbeat_manager
        self.checkpoint_manager = checkpoint_manager
        self._failover_records: dict[str, list[FailoverRecord]] = {}

    def detect_failure(self) -> list[WorkerInfo]:
        """检测故障节点

        调用心跳管理器获取不健康的工作节点列表。

        Returns:
            不健康的工作节点列表
        """
        unhealthy_workers = self.heartbeat_manager.get_unhealthy_workers()
        if unhealthy_workers:
            logger.warning(
                "检测到不健康节点: count=%d, ids=%s",
                len(unhealthy_workers),
                [w.worker_id for w in unhealthy_workers],
            )
        return unhealthy_workers

    def execute_failover(
        self,
        worker_id: str,
        reason: str,
        operator: str | None = None,
    ) -> FailoverRecord:
        """执行故障转移

        Args:
            worker_id: 故障工作节点标识
            reason: 故障转移原因
            operator: 操作者标识

        Returns:
            故障转移记录

        Raises:
            KeyError: 工作节点未注册
        """
        # 获取工作节点信息
        workers = self.heartbeat_manager.list_workers()
        worker = next(
            (w for w in workers if w.worker_id == worker_id),
            None,
        )
        if worker is None:
            raise KeyError(f"工作节点未注册: {worker_id}")

        # 记录原始状态并执行故障转移
        from_state = self._resolve_failover_state(worker.status)
        now = datetime.now(UTC)

        # 更新节点状态为故障
        worker.status = WorkerHealthStatus.UNHEALTHY
        worker.fail_count += 1
        worker.touch()

        # 创建故障转移记录
        record = FailoverRecord(
            worker_id=worker_id,
            from_state=from_state,
            to_state=FailoverState.FAILOVER,
            reason=reason,
            completed_at=now,
            created_by=operator,
            updated_by=operator,
        )

        if worker_id not in self._failover_records:
            self._failover_records[worker_id] = []
        self._failover_records[worker_id].append(record)

        logger.error(
            "故障转移已执行: worker_id=%s, from=%s, to=%s, reason=%s",
            worker_id,
            from_state.value,
            FailoverState.FAILOVER.value,
            reason,
        )
        return record

    def recover_worker(
        self,
        worker_id: str,
        operator: str | None = None,
    ) -> FailoverRecord:
        """恢复工作节点

        Args:
            worker_id: 工作节点标识
            operator: 操作者标识

        Returns:
            故障转移记录

        Raises:
            KeyError: 工作节点未注册
        """
        workers = self.heartbeat_manager.list_workers()
        worker = next(
            (w for w in workers if w.worker_id == worker_id),
            None,
        )
        if worker is None:
            raise KeyError(f"工作节点未注册: {worker_id}")

        # 恢复节点健康状态
        previous_state = self._resolve_failover_state(worker.status)
        worker.status = WorkerHealthStatus.HEALTHY
        worker.fail_count = 0
        worker.touch()

        now = datetime.now(UTC)
        record = FailoverRecord(
            worker_id=worker_id,
            from_state=previous_state,
            to_state=FailoverState.RECOVERED,
            reason="手动恢复",
            completed_at=now,
            created_by=operator,
            updated_by=operator,
        )

        if worker_id not in self._failover_records:
            self._failover_records[worker_id] = []
        self._failover_records[worker_id].append(record)

        logger.info(
            "工作节点已恢复: worker_id=%s, from=%s, to=%s",
            worker_id,
            previous_state.value,
            FailoverState.RECOVERED.value,
        )
        return record

    def get_failover_history(
        self,
        worker_id: str,
    ) -> list[FailoverRecord]:
        """获取工作节点的故障转移历史

        Args:
            worker_id: 工作节点标识

        Returns:
            故障转移记录列表
        """
        return self._failover_records.get(worker_id, [])

    @staticmethod
    def _resolve_failover_state(health_status: WorkerHealthStatus) -> FailoverState:
        """根据健康状态推断故障转移状态

        Args:
            health_status: 工作节点健康状态

        Returns:
            对应的故障转移状态
        """
        mapping = {
            WorkerHealthStatus.HEALTHY: FailoverState.PRIMARY,
            WorkerHealthStatus.DEGRADED: FailoverState.SECONDARY,
            WorkerHealthStatus.UNHEALTHY: FailoverState.FAILOVER,
            WorkerHealthStatus.DEAD: FailoverState.FAILOVER,
        }
        return mapping.get(health_status, FailoverState.PRIMARY)
