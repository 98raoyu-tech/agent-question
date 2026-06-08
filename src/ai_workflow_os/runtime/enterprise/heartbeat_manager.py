"""
企业级心跳管理器

提供工作节点的注册、心跳记录、健康检测和注销功能。
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from ...platform.common.base_entity import BaseEntity
from .enums import WorkerHealthStatus

logger = logging.getLogger(__name__)


@dataclass
class WorkerInfo(BaseEntity):
    """工作节点信息实体

    记录工作节点的连接信息、健康状态和心跳数据。

    Attributes:
        worker_id: 工作节点标识
        host: 主机地址
        port: 端口号
        status: 健康状态
        last_heartbeat: 最后心跳时间
        fail_count: 连续失败次数
    """

    worker_id: str = ""
    host: str = ""
    port: int = 0
    status: WorkerHealthStatus = WorkerHealthStatus.HEALTHY
    last_heartbeat: datetime | None = None
    fail_count: int = 0


class HeartbeatManager:
    """心跳管理器

    管理工作节点的注册、心跳记录、健康状态检测和注销。
    """

    def __init__(self) -> None:
        """初始化工作节点存储"""
        self._workers: dict[str, WorkerInfo] = {}

    def register_worker(
        self,
        worker_id: str,
        host: str,
        port: int,
    ) -> WorkerInfo:
        """注册工作节点

        Args:
            worker_id: 工作节点标识
            host: 主机地址
            port: 端口号

        Returns:
            注册的工作节点信息
        """
        now = datetime.now(UTC)
        worker = WorkerInfo(
            worker_id=worker_id,
            host=host,
            port=port,
            status=WorkerHealthStatus.HEALTHY,
            last_heartbeat=now,
            fail_count=0,
        )
        self._workers[worker_id] = worker
        logger.info(
            "工作节点注册成功: worker_id=%s, host=%s:%d",
            worker_id,
            host,
            port,
        )
        return worker

    def record_heartbeat(self, worker_id: str) -> WorkerInfo:
        """记录心跳

        Args:
            worker_id: 工作节点标识

        Returns:
            更新后的工作节点信息

        Raises:
            KeyError: 工作节点未注册
        """
        worker = self._workers.get(worker_id)
        if worker is None:
            raise KeyError(f"工作节点未注册: {worker_id}")

        worker.last_heartbeat = datetime.now(UTC)
        worker.fail_count = 0
        worker.status = WorkerHealthStatus.HEALTHY
        worker.touch()
        return worker

    def get_unhealthy_workers(
        self,
        timeout_seconds: int = 30,
    ) -> list[WorkerInfo]:
        """获取不健康的工作节点

        Args:
            timeout_seconds: 心跳超时时间（秒）

        Returns:
            不健康的工作节点列表
        """
        now = datetime.now(UTC)
        unhealthy_workers: list[WorkerInfo] = []

        for worker in self._workers.values():
            if worker.is_deleted:
                continue

            # 未收到心跳或心跳超时的节点标记为不健康
            if worker.last_heartbeat is None:
                worker.status = WorkerHealthStatus.DEAD
                unhealthy_workers.append(worker)
                continue

            elapsed = (now - worker.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                # 根据超时时长分级判断健康状态
                if elapsed > timeout_seconds * 3:
                    worker.status = WorkerHealthStatus.DEAD
                elif elapsed > timeout_seconds * 2:
                    worker.status = WorkerHealthStatus.UNHEALTHY
                else:
                    worker.status = WorkerHealthStatus.DEGRADED
                unhealthy_workers.append(worker)

        return unhealthy_workers

    def list_workers(self) -> list[WorkerInfo]:
        """列出所有已注册的工作节点

        Returns:
            工作节点列表
        """
        return [
            w for w in self._workers.values()
            if not w.is_deleted
        ]

    def deregister_worker(self, worker_id: str) -> bool:
        """注销工作节点

        Args:
            worker_id: 工作节点标识

        Returns:
            是否注销成功
        """
        worker = self._workers.get(worker_id)
        if worker is None:
            logger.warning("注销失败，工作节点未注册: worker_id=%s", worker_id)
            return False

        worker.mark_deleted()
        logger.info("工作节点已注销: worker_id=%s", worker_id)
        return True
