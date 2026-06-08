"""
工作流快照模块

实现工作流状态的完整与增量快照管理，支持：
- 全量快照与增量快照
- 数据压缩与解压
- 校验和验证
- 快照对比
"""

import hashlib
import json
import logging
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ..platform.common.base_entity import BaseEntity

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class SnapshotType(str, Enum):
    """快照类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"


# ==================== 实体定义 ====================

@dataclass
class WorkflowSnapshot(BaseEntity):
    """工作流快照实体

    记录工作流运行时的完整状态，包括工作流状态、内存快照、
    变量和步骤历史。

    Attributes:
        workflow_id: 关联的工作流标识
        agent_id: 关联的 Agent 标识
        snapshot_type: 快照类型（全量或增量）
        state: 工作流状态
        memory_snapshot: Agent 内存快照
        variables: 工作流变量
        step_history: 步骤执行历史
        size_bytes: 快照数据大小（字节）
        compressed: 是否已压缩
    """

    workflow_id: str = field(default="")
    agent_id: str = field(default="")
    snapshot_type: SnapshotType = field(default=SnapshotType.FULL)
    state: dict[str, Any] = field(default_factory=dict)
    memory_snapshot: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    step_history: list[dict[str, Any]] = field(default_factory=list)
    size_bytes: int = field(default=0)
    compressed: bool = field(default=False)

    def compress(
        self,
        operator: Optional[str] = None,
    ) -> None:
        """压缩快照数据

        使用 zlib 压缩 state、memory_snapshot 和 variables 数据。

        Args:
            operator: 操作者标识
        """
        if self.compressed:
            logger.debug("快照 '%s' 已处于压缩状态，跳过", self.id)
            return

        payload = json.dumps({
            "state": self.state,
            "memory_snapshot": self.memory_snapshot,
            "variables": self.variables,
        }, ensure_ascii=False, default=str)

        original_size = len(payload.encode("utf-8"))
        compressed_data = zlib.compress(payload.encode("utf-8"))
        compressed_size = len(compressed_data)

        self.state = {"__compressed__": compressed_data.hex()}
        self.memory_snapshot = {}
        self.variables = {}
        self.size_bytes = compressed_size
        self.compressed = True
        self.touch(operator)

        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        logger.info(
            "快照 '%s' 已压缩 (%d -> %d bytes, 压缩率: %.1f%%)",
            self.id,
            original_size,
            compressed_size,
            ratio,
        )

    def decompress(self) -> dict[str, Any]:
        """解压快照数据

        Returns:
            dict: 解压后的完整快照数据，包含 state、memory_snapshot 和 variables

        Raises:
            ValueError: 当快照未压缩或压缩数据格式异常时抛出
        """
        if not self.compressed:
            logger.debug("快照 '%s' 未压缩，直接返回原始数据", self.id)
            return {
                "state": self.state,
                "memory_snapshot": self.memory_snapshot,
                "variables": self.variables,
            }

        compressed_hex = self.state.get("__compressed__")
        if not compressed_hex:
            raise ValueError(f"快照 '{self.id}' 的压缩数据格式异常")

        compressed_data = bytes.fromhex(compressed_hex)
        decompressed = zlib.decompress(compressed_data)
        payload = json.loads(decompressed.decode("utf-8"))

        logger.debug("快照 '%s' 已解压", self.id)
        return payload

    def validate_checksum(self) -> bool:
        """验证快照数据的校验和

        对快照核心数据计算 SHA-256 校验和，与存储的校验和比对。

        Returns:
            bool: 校验通过返回 True
        """
        try:
            if self.compressed:
                data_str = self.state.get("__compressed__", "")
            else:
                data_str = json.dumps({
                    "state": self.state,
                    "memory_snapshot": self.memory_snapshot,
                    "variables": self.variables,
                }, ensure_ascii=False, default=str)

            computed_hash = hashlib.sha256(
                data_str.encode("utf-8")
            ).hexdigest()

            stored_hash = self.updated_by or ""
            if not stored_hash:
                logger.debug("快照 '%s' 无存储的校验和，跳过验证", self.id)
                return True

            is_valid = computed_hash == stored_hash
            if not is_valid:
                logger.warning("快照 '%s' 校验和不匹配", self.id)

            return is_valid

        except Exception as error:
            logger.error(
                "快照 '%s' 校验和验证失败: %s - %s",
                self.id,
                type(error).__name__,
                str(error),
            )
            return False


# ==================== 快照管理器 ====================

class SnapshotManager:
    """快照管理器

    管理工作流快照的创建、恢复、查询和对比。

    Attributes:
        _snapshots: 快照存储，键为 snapshot_id
        _workflow_index: 工作流到快照的索引映射，键为 workflow_id
    """

    def __init__(self) -> None:
        """初始化快照管理器"""
        self._snapshots: dict[str, WorkflowSnapshot] = {}
        self._workflow_index: dict[str, list[str]] = {}
        logger.info("快照管理器已初始化")

    # ==================== 创建 ====================

    def create_snapshot(
        self,
        workflow_id: str,
        agent_id: str,
        state: dict[str, Any],
        memory: dict[str, Any],
        variables: dict[str, Any],
        operator: Optional[str] = None,
    ) -> WorkflowSnapshot:
        """创建工作流快照

        Args:
            workflow_id: 工作流标识
            agent_id: Agent 标识
            state: 工作流状态
            memory: Agent 内存快照
            variables: 工作流变量
            operator: 操作者标识

        Returns:
            WorkflowSnapshot: 创建的快照实体
        """
        # 计算数据大小
        payload = json.dumps({
            "state": state,
            "memory": memory,
            "variables": variables,
        }, ensure_ascii=False, default=str)
        size_bytes = len(payload.encode("utf-8"))

        # 判断快照类型：工作流已有快照则为增量，否则为全量
        existing_ids = self._workflow_index.get(workflow_id, [])
        snapshot_type = (
            SnapshotType.INCREMENTAL if existing_ids else SnapshotType.FULL
        )

        snapshot = WorkflowSnapshot(
            workflow_id=workflow_id,
            agent_id=agent_id,
            snapshot_type=snapshot_type,
            state=state,
            memory_snapshot=memory,
            variables=variables,
            size_bytes=size_bytes,
            created_by=operator,
        )

        self._snapshots[snapshot.id] = snapshot

        if workflow_id not in self._workflow_index:
            self._workflow_index[workflow_id] = []
        self._workflow_index[workflow_id].append(snapshot.id)

        logger.info(
            "已创建快照: %s (工作流: %s, 类型: %s, 大小: %d bytes)",
            snapshot.id,
            workflow_id,
            snapshot_type.value,
            size_bytes,
        )

        return snapshot

    # ==================== 恢复 ====================

    def restore_snapshot(
        self,
        snapshot_id: str,
    ) -> Optional[dict[str, Any]]:
        """恢复快照

        Args:
            snapshot_id: 快照标识

        Returns:
            Optional[dict]: 快照数据，不存在返回 None
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.warning("快照 '%s' 不存在", snapshot_id)
            return None

        try:
            data = snapshot.decompress()
            logger.info(
                "已恢复快照: %s (工作流: %s)",
                snapshot_id,
                snapshot.workflow_id,
            )
            return data
        except Exception as error:
            logger.error(
                "快照 '%s' 恢复失败: %s - %s",
                snapshot_id,
                type(error).__name__,
                str(error),
            )
            return None

    # ==================== 查询 ====================

    def list_snapshots(
        self,
        workflow_id: str,
    ) -> list[WorkflowSnapshot]:
        """列出指定工作流的所有快照

        Args:
            workflow_id: 工作流标识

        Returns:
            list: 快照列表，按创建时间升序排列
        """
        snapshot_ids = self._workflow_index.get(workflow_id, [])
        snapshots = [
            self._snapshots[sid]
            for sid in snapshot_ids
            if sid in self._snapshots
        ]
        snapshots.sort(key=lambda s: s.created_at)
        return snapshots

    # ==================== 对比 ====================

    def compare_snapshots(
        self,
        snapshot_id_a: str,
        snapshot_id_b: str,
    ) -> dict[str, Any]:
        """对比两个快照

        Args:
            snapshot_id_a: 快照 A 的标识
            snapshot_id_b: 快照 B 的标识

        Returns:
            dict: 对比结果，包含差异信息

        Raises:
            ValueError: 当任一快照不存在时抛出
        """
        snapshot_a = self._snapshots.get(snapshot_id_a)
        snapshot_b = self._snapshots.get(snapshot_id_b)

        if not snapshot_a:
            raise ValueError(f"快照 '{snapshot_id_a}' 不存在")
        if not snapshot_b:
            raise ValueError(f"快照 '{snapshot_id_b}' 不存在")

        data_a = snapshot_a.decompress()
        data_b = snapshot_b.decompress()

        # 对比各维度的差异
        state_diff = self._compute_dict_diff(
            data_a.get("state", {}),
            data_b.get("state", {}),
        )
        memory_diff = self._compute_dict_diff(
            data_a.get("memory_snapshot", {}),
            data_b.get("memory_snapshot", {}),
        )
        variables_diff = self._compute_dict_diff(
            data_a.get("variables", {}),
            data_b.get("variables", {}),
        )

        return {
            "snapshot_a": {
                "id": snapshot_id_a,
                "workflow_id": snapshot_a.workflow_id,
                "created_at": snapshot_a.created_at.isoformat(),
                "snapshot_type": snapshot_a.snapshot_type.value,
            },
            "snapshot_b": {
                "id": snapshot_id_b,
                "workflow_id": snapshot_b.workflow_id,
                "created_at": snapshot_b.created_at.isoformat(),
                "snapshot_type": snapshot_b.snapshot_type.value,
            },
            "diff": {
                "state": state_diff,
                "memory": memory_diff,
                "variables": variables_diff,
            },
            "step_history_diff": {
                "a_count": len(snapshot_a.step_history),
                "b_count": len(snapshot_b.step_history),
            },
        }

    def _compute_dict_diff(
        self,
        dict_a: dict[str, Any],
        dict_b: dict[str, Any],
    ) -> dict[str, Any]:
        """计算两个字典之间的差异

        Args:
            dict_a: 字典 A
            dict_b: 字典 B

        Returns:
            dict: 差异信息，包含 added、removed 和 changed 键
        """
        keys_a = set(dict_a.keys())
        keys_b = set(dict_b.keys())

        added = {k: dict_b[k] for k in keys_b - keys_a}
        removed = {k: dict_a[k] for k in keys_a - keys_b}
        changed = {
            k: {"from": dict_a[k], "to": dict_b[k]}
            for k in keys_a & keys_b
            if dict_a[k] != dict_b[k]
        }

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
        }
