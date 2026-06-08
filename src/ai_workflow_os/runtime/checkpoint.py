"""
检查点模块

实现工作流执行过程中的检查点管理，支持：
- 多种检查点类型（步骤、定时、手动）
- 状态与上下文快照
- 检查点验证与失效
- 检查点生命周期管理
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ..platform.common.base_entity import BaseEntity

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class CheckpointType(str, Enum):
    """检查点类型枚举"""
    STEP = "step"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


# ==================== 实体定义 ====================

@dataclass
class Checkpoint(BaseEntity):
    """检查点实体

    记录工作流执行过程中的状态快照，用于故障恢复和回溯。

    Attributes:
        task_id: 关联的任务标识
        workflow_id: 关联的工作流标识
        checkpoint_type: 检查点类型
        state_snapshot: 工作流状态快照
        context_snapshot: 执行上下文快照
        step_index: 当前步骤索引
        step_name: 当前步骤名称
        is_valid: 检查点是否有效
    """

    task_id: str = field(default="")
    workflow_id: str = field(default="")
    checkpoint_type: CheckpointType = field(default=CheckpointType.STEP)
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    step_index: int = field(default=0)
    step_name: str = field(default="")
    is_valid: bool = field(default=True)

    def validate(self) -> bool:
        """验证检查点的有效性

        检查必填字段是否完整且检查点未被失效。

        Returns:
            bool: 检查点有效返回 True
        """
        if not self.is_valid:
            logger.debug("检查点 '%s' 已失效", self.id)
            return False

        if not self.task_id or not self.workflow_id:
            logger.warning("检查点 '%s' 缺少必要的 task_id 或 workflow_id", self.id)
            return False

        if not self.state_snapshot:
            logger.warning("检查点 '%s' 的 state_snapshot 为空", self.id)
            return False

        return True

    def invalidate(
        self,
        operator: Optional[str] = None,
    ) -> None:
        """使检查点失效

        Args:
            operator: 操作者标识
        """
        self.is_valid = False
        self.touch(operator)
        logger.info("检查点 '%s' 已失效 (操作者: %s)", self.id, operator)

    def to_dict(self) -> dict[str, Any]:
        """将检查点转换为字典

        Returns:
            dict: 检查点的字典表示
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "checkpoint_type": self.checkpoint_type.value,
            "state_snapshot": self.state_snapshot,
            "context_snapshot": self.context_snapshot,
            "step_index": self.step_index,
            "step_name": self.step_name,
            "created_at": self.created_at.isoformat(),
            "is_valid": self.is_valid,
            "version": self.version,
        }


# ==================== 检查点管理器 ====================

class CheckpointManager:
    """检查点管理器

    管理检查点的创建、恢复、查询和清理。

    Attributes:
        _checkpoints: 检查点存储，键为 checkpoint_id
        _task_index: 任务到检查点的索引映射，键为 task_id
    """

    def __init__(self) -> None:
        """初始化检查点管理器"""
        self._checkpoints: dict[str, Checkpoint] = {}
        self._task_index: dict[str, list[str]] = {}
        logger.info("检查点管理器已初始化")

    # ==================== 创建 ====================

    def create_checkpoint(
        self,
        task_id: str,
        workflow_id: str,
        state: dict[str, Any],
        context: dict[str, Any],
        step: dict[str, Any],
        operator: Optional[str] = None,
    ) -> Checkpoint:
        """创建检查点

        Args:
            task_id: 任务标识
            workflow_id: 工作流标识
            state: 工作流状态快照
            context: 执行上下文快照
            step: 步骤信息，包含 index 和 name
            operator: 操作者标识

        Returns:
            Checkpoint: 创建的检查点实体
        """
        checkpoint = Checkpoint(
            task_id=task_id,
            workflow_id=workflow_id,
            checkpoint_type=CheckpointType.STEP,
            state_snapshot=state,
            context_snapshot=context,
            step_index=step.get("index", 0),
            step_name=step.get("name", ""),
            created_by=operator,
        )

        self._checkpoints[checkpoint.id] = checkpoint

        if task_id not in self._task_index:
            self._task_index[task_id] = []
        self._task_index[task_id].append(checkpoint.id)

        logger.info(
            "已创建检查点: %s (任务: %s, 步骤: %s, 操作者: %s)",
            checkpoint.id,
            task_id,
            step.get("name", ""),
            operator,
        )

        return checkpoint

    # ==================== 恢复 ====================

    def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[Checkpoint]:
        """恢复检查点

        Args:
            checkpoint_id: 检查点标识

        Returns:
            Optional[Checkpoint]: 有效的检查点实体，不存在或已失效返回 None
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            logger.warning("检查点 '%s' 不存在", checkpoint_id)
            return None

        if not checkpoint.validate():
            logger.warning("检查点 '%s' 无效，无法恢复", checkpoint_id)
            return None

        logger.info("已恢复检查点: %s (任务: %s)", checkpoint_id, checkpoint.task_id)
        return checkpoint

    # ==================== 查询 ====================

    def list_checkpoints(
        self,
        task_id: str,
    ) -> list[Checkpoint]:
        """列出指定任务的所有检查点

        Args:
            task_id: 任务标识

        Returns:
            list: 检查点列表，按创建时间升序排列
        """
        checkpoint_ids = self._task_index.get(task_id, [])
        checkpoints = [
            self._checkpoints[cid]
            for cid in checkpoint_ids
            if cid in self._checkpoints
        ]
        checkpoints.sort(key=lambda cp: cp.created_at)
        return checkpoints

    # ==================== 删除 ====================

    def delete_checkpoints(
        self,
        task_id: str,
        operator: Optional[str] = None,
    ) -> int:
        """删除指定任务的所有检查点

        Args:
            task_id: 任务标识
            operator: 操作者标识

        Returns:
            int: 删除的检查点数量
        """
        checkpoint_ids = self._task_index.get(task_id, [])
        deleted_count = 0

        for cid in checkpoint_ids:
            if cid in self._checkpoints:
                self._checkpoints[cid].mark_deleted(operator)
                del self._checkpoints[cid]
                deleted_count += 1

        if task_id in self._task_index:
            del self._task_index[task_id]

        logger.info(
            "已删除任务 '%s' 的 %d 个检查点 (操作者: %s)",
            task_id,
            deleted_count,
            operator,
        )

        return deleted_count

    # ==================== 清理 ====================

    def cleanup_expired(
        self,
        max_age_hours: int = 24,
        operator: Optional[str] = None,
    ) -> int:
        """清理过期的检查点

        删除创建时间超过指定时长的检查点。

        Args:
            max_age_hours: 最大保留时长（小时）
            operator: 操作者标识

        Returns:
            int: 清理的检查点数量
        """
        now = datetime.now(timezone.utc)
        expired_ids: list[str] = []

        for checkpoint_id, checkpoint in self._checkpoints.items():
            age_hours = (now - checkpoint.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                expired_ids.append(checkpoint_id)

        for cid in expired_ids:
            checkpoint = self._checkpoints[cid]
            checkpoint.mark_deleted(operator)

            # 从索引中移除
            task_id = checkpoint.task_id
            if task_id in self._task_index:
                self._task_index[task_id] = [
                    rid for rid in self._task_index[task_id] if rid != cid
                ]

            del self._checkpoints[cid]

        logger.info(
            "已清理 %d 个过期检查点 (最大保留: %d 小时, 操作者: %s)",
            len(expired_ids),
            max_age_hours,
            operator,
        )

        return len(expired_ids)
