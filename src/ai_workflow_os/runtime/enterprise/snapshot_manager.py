"""
企业级快照管理器

提供运行时状态的全量、增量和差异快照管理功能。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from ...platform.common.base_entity import BaseEntity
from .enums import SnapshotType

logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot(BaseEntity):
    """状态快照实体

    记录Agent在特定时间点的运行时状态，支持全量、增量和差异快照。

    Attributes:
        agent_id: 关联的Agent标识
        snapshot_type: 快照类型
        state_data: 状态数据
        metadata: 扩展元数据
    """

    agent_id: str = ""
    snapshot_type: SnapshotType = SnapshotType.FULL
    state_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class SnapshotManager:
    """快照管理器

    管理Agent运行时状态快照的完整生命周期，包括创建、恢复、查询和差异比较。
    """

    def __init__(self) -> None:
        """初始化快照存储"""
        self._snapshots: dict[str, StateSnapshot] = {}

    def create_snapshot(
        self,
        snapshot_type: SnapshotType,
        state_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        operator: str | None = None,
    ) -> StateSnapshot:
        """创建快照

        Args:
            snapshot_type: 快照类型
            state_data: 当前状态数据
            metadata: 扩展元数据
            operator: 操作者标识

        Returns:
            创建的快照实体
        """
        snapshot = StateSnapshot(
            snapshot_type=snapshot_type,
            state_data=state_data,
            metadata=metadata or {},
            created_by=operator,
            updated_by=operator,
        )
        self._snapshots[snapshot.id] = snapshot
        logger.info(
            "快照创建成功: id=%s, type=%s",
            snapshot.id,
            snapshot_type.value,
        )
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> StateSnapshot:
        """恢复快照

        Args:
            snapshot_id: 快照标识

        Returns:
            恢复的快照实体

        Raises:
            KeyError: 快照不存在
        """
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise KeyError(f"快照不存在: {snapshot_id}")

        snapshot.touch()
        logger.info(
            "快照恢复成功: id=%s, type=%s",
            snapshot.id,
            snapshot.snapshot_type.value,
        )
        return snapshot

    def list_snapshots(self, agent_id: str) -> list[StateSnapshot]:
        """查询Agent的所有快照

        Args:
            agent_id: Agent标识

        Returns:
            快照列表
        """
        return [
            snap
            for snap in self._snapshots.values()
            if snap.agent_id == agent_id and not snap.is_deleted
        ]

    def diff_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
    ) -> dict[str, Any]:
        """比较两个快照的差异

        Args:
            snapshot_id_1: 第一个快照标识
            snapshot_id_2: 第二个快照标识

        Returns:
            差异结果字典，包含 added、removed、changed 三个维度

        Raises:
            KeyError: 快照不存在
        """
        snapshot_1 = self._snapshots.get(snapshot_id_1)
        snapshot_2 = self._snapshots.get(snapshot_id_2)

        if snapshot_1 is None:
            raise KeyError(f"快照不存在: {snapshot_id_1}")
        if snapshot_2 is None:
            raise KeyError(f"快照不存在: {snapshot_id_2}")

        # 计算两个快照状态数据之间的差异
        data_1 = snapshot_1.state_data
        data_2 = snapshot_2.state_data

        keys_1 = set(data_1.keys())
        keys_2 = set(data_2.keys())

        added = {k: data_2[k] for k in keys_2 - keys_1}
        removed = {k: data_1[k] for k in keys_1 - keys_2}
        changed = {
            k: {"old": data_1[k], "new": data_2[k]}
            for k in keys_1 & keys_2
            if data_1[k] != data_2[k]
        }

        return {
            "snapshot_1_id": snapshot_id_1,
            "snapshot_2_id": snapshot_id_2,
            "added": added,
            "removed": removed,
            "changed": changed,
        }
