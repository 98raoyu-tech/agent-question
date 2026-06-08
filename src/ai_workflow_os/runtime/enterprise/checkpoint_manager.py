"""
企业级检查点管理器

提供任务状态的检查点创建、恢复、查询和过期清理功能。
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from ...platform.common.base_entity import BaseEntity
from .enums import CheckpointStatus

logger = logging.getLogger(__name__)


@dataclass
class TaskCheckpoint(BaseEntity):
    """任务检查点实体

    记录任务在特定时间点的状态快照，支持状态恢复和过期清理。

    Attributes:
        task_id: 关联的任务标识
        checkpoint_data: 检查点状态数据
        status: 检查点状态
        expires_at: 过期时间
    """

    task_id: str = ""
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    status: CheckpointStatus = CheckpointStatus.CREATED
    expires_at: datetime | None = None


class CheckpointManager:
    """检查点管理器

    管理任务检查点的完整生命周期，包括创建、恢复、查询和过期清理。
    """

    def __init__(self) -> None:
        """初始化检查点存储"""
        self._checkpoints: dict[str, TaskCheckpoint] = {}

    def create_checkpoint(
        self,
        task_id: str,
        state_data: dict[str, Any],
        operator: str | None = None,
    ) -> TaskCheckpoint:
        """创建检查点

        Args:
            task_id: 任务标识
            state_data: 当前状态数据
            operator: 操作者标识

        Returns:
            创建的检查点实体
        """
        checkpoint = TaskCheckpoint(
            task_id=task_id,
            checkpoint_data=state_data,
            status=CheckpointStatus.CREATED,
            created_by=operator,
            updated_by=operator,
        )
        self._checkpoints[checkpoint.id] = checkpoint
        logger.info(
            "检查点创建成功: id=%s, task_id=%s",
            checkpoint.id,
            task_id,
        )
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> TaskCheckpoint:
        """恢复检查点

        Args:
            checkpoint_id: 检查点标识

        Returns:
            恢复的检查点实体

        Raises:
            KeyError: 检查点不存在
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint is None:
            raise KeyError(f"检查点不存在: {checkpoint_id}")

        checkpoint.status = CheckpointStatus.RESTORED
        checkpoint.touch()
        logger.info(
            "检查点恢复成功: id=%s, task_id=%s",
            checkpoint.id,
            checkpoint.task_id,
        )
        return checkpoint

    def list_checkpoints(self, task_id: str) -> list[TaskCheckpoint]:
        """查询任务的所有检查点

        Args:
            task_id: 任务标识

        Returns:
            检查点列表
        """
        return [
            cp
            for cp in self._checkpoints.values()
            if cp.task_id == task_id and not cp.is_deleted
        ]

    def cleanup_expired_checkpoints(self, max_age_hours: int = 24) -> int:
        """清理过期检查点

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的检查点数量
        """
        # 计算过期阈值时间
        threshold = datetime.now(UTC) - timedelta(hours=max_age_hours)
        cleaned_count = 0

        for checkpoint in self._checkpoints.values():
            if checkpoint.is_deleted:
                continue
            if checkpoint.created_at < threshold:
                checkpoint.status = CheckpointStatus.EXPIRED
                checkpoint.mark_deleted()
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(
                "过期检查点清理完成: 清理数量=%d, 阈值=%d小时",
                cleaned_count,
                max_age_hours,
            )

        return cleaned_count
