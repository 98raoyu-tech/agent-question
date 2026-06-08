"""
任务恢复模块

实现失败任务的自动恢复与重试机制，支持：
- 从检查点恢复任务
- 延迟调度恢复
- 任务重试
- 恢复状态查询
- 恢复策略配置
"""

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class RecoveryStrategy(str, Enum):
    """恢复策略枚举"""
    RETRY_FROM_CHECKPOINT = "retry_from_checkpoint"
    RETRY_FROM_BEGINNING = "retry_from_beginning"
    SKIP = "skip"
    ABORT = "abort"


class RecoveryStatus(str, Enum):
    """恢复状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABORTED = "aborted"


# ==================== 任务恢复管理器 ====================

class TaskRecoveryManager:
    """任务恢复管理器

    管理失败任务的恢复策略，支持从检查点恢复、延迟调度和重试。

    Attributes:
        recovery_strategies: 任务恢复策略映射，键为 task_id
        max_retry_count: 最大重试次数
        recovery_queue: 恢复任务队列
        _retry_counts: 任务重试计数映射，键为 task_id
        _recovery_status: 任务恢复状态映射，键为 task_id
    """

    def __init__(
        self,
        max_retry_count: int = 3,
    ) -> None:
        """初始化任务恢复管理器

        Args:
            max_retry_count: 最大重试次数
        """
        self.recovery_strategies: dict[str, str] = {}
        self.max_retry_count: int = max_retry_count
        self.recovery_queue: list[dict[str, Any]] = []
        self._retry_counts: dict[str, int] = {}
        self._recovery_status: dict[str, dict[str, Any]] = {}
        logger.info(
            "任务恢复管理器已初始化 (最大重试次数: %d)",
            max_retry_count,
        )

    # ==================== 恢复策略配置 ====================

    def set_recovery_strategy(
        self,
        task_id: str,
        strategy: str,
        operator: Optional[str] = None,
    ) -> None:
        """设置任务的恢复策略

        Args:
            task_id: 任务标识
            strategy: 恢复策略（retry_from_checkpoint、retry_from_beginning、skip、abort）
            operator: 操作者标识
        """
        valid_strategies = [s.value for s in RecoveryStrategy]
        if strategy not in valid_strategies:
            raise ValueError(
                f"无效的恢复策略: '{strategy}'，"
                f"有效值: {valid_strategies}"
            )

        self.recovery_strategies[task_id] = strategy
        logger.info(
            "已设置任务 '%s' 的恢复策略: %s (操作者: %s)",
            task_id,
            strategy,
            operator,
        )

    # ==================== 任务恢复 ====================

    def recover_task(
        self,
        task_id: str,
        checkpoint_id: str,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """从检查点恢复任务

        Args:
            task_id: 任务标识
            checkpoint_id: 检查点标识
            operator: 操作者标识

        Returns:
            dict: 恢复结果
        """
        # 检查重试次数
        current_retries = self._retry_counts.get(task_id, 0)
        if current_retries >= self.max_retry_count:
            status = RecoveryStatus.ABORTED
            self._recovery_status[task_id] = {
                "task_id": task_id,
                "status": status.value,
                "checkpoint_id": checkpoint_id,
                "retry_count": current_retries,
                "reason": f"超过最大重试次数 ({self.max_retry_count})",
                "recovered_at": datetime.now(timezone.utc).isoformat(),
                "operator": operator,
            }
            logger.error(
                "任务 '%s' 恢复失败: 超过最大重试次数 (%d/%d)",
                task_id,
                current_retries,
                self.max_retry_count,
            )
            return self._recovery_status[task_id]

        # 执行恢复
        self._retry_counts[task_id] = current_retries + 1
        status = RecoveryStatus.IN_PROGRESS

        self._recovery_status[task_id] = {
            "task_id": task_id,
            "status": status.value,
            "checkpoint_id": checkpoint_id,
            "retry_count": self._retry_counts[task_id],
            "recovered_at": datetime.now(timezone.utc).isoformat(),
            "operator": operator,
        }

        logger.info(
            "任务 '%s' 正在从检查点 '%s' 恢复 (重试: %d/%d, 操作者: %s)",
            task_id,
            checkpoint_id,
            self._retry_counts[task_id],
            self.max_retry_count,
            operator,
        )

        return self._recovery_status[task_id]

    # ==================== 延迟调度 ====================

    def schedule_recovery(
        self,
        task_id: str,
        delay_seconds: int,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """延迟调度任务恢复

        将任务加入恢复队列，设定延迟时间后执行恢复。

        Args:
            task_id: 任务标识
            delay_seconds: 延迟时间（秒）
            operator: 操作者标识

        Returns:
            dict: 调度结果
        """
        now = datetime.now(timezone.utc)
        scheduled_at = datetime.fromtimestamp(
            time.time() + delay_seconds,
            tz=timezone.utc,
        )

        queue_entry = {
            "task_id": task_id,
            "delay_seconds": delay_seconds,
            "scheduled_at": scheduled_at.isoformat(),
            "created_at": now.isoformat(),
            "operator": operator,
            "status": RecoveryStatus.PENDING.value,
        }

        self.recovery_queue.append(queue_entry)

        self._recovery_status[task_id] = {
            "task_id": task_id,
            "status": RecoveryStatus.PENDING.value,
            "delay_seconds": delay_seconds,
            "scheduled_at": scheduled_at.isoformat(),
            "operator": operator,
        }

        logger.info(
            "任务 '%s' 已加入恢复队列 (延迟: %ds, 预计执行: %s, 操作者: %s)",
            task_id,
            delay_seconds,
            scheduled_at.isoformat(),
            operator,
        )

        return queue_entry

    # ==================== 重试 ====================

    def retry_task(
        self,
        task_id: str,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """重试任务

        根据配置的恢复策略重新执行任务。

        Args:
            task_id: 任务标识
            operator: 操作者标识

        Returns:
            dict: 重试结果
        """
        current_retries = self._retry_counts.get(task_id, 0)

        # 检查重试次数限制
        if current_retries >= self.max_retry_count:
            self._recovery_status[task_id] = {
                "task_id": task_id,
                "status": RecoveryStatus.ABORTED.value,
                "retry_count": current_retries,
                "reason": f"超过最大重试次数 ({self.max_retry_count})",
                "retried_at": datetime.now(timezone.utc).isoformat(),
                "operator": operator,
            }
            logger.error(
                "任务 '%s' 重试失败: 超过最大重试次数 (%d/%d)",
                task_id,
                current_retries,
                self.max_retry_count,
            )
            return self._recovery_status[task_id]

        # 获取恢复策略
        strategy = self.recovery_strategies.get(
            task_id,
            RecoveryStrategy.RETRY_FROM_CHECKPOINT.value,
        )

        self._retry_counts[task_id] = current_retries + 1

        # 根据策略处理
        if strategy == RecoveryStrategy.SKIP.value:
            status = RecoveryStatus.SKIPPED
        elif strategy == RecoveryStrategy.ABORT.value:
            status = RecoveryStatus.ABORTED
        else:
            status = RecoveryStatus.IN_PROGRESS

        self._recovery_status[task_id] = {
            "task_id": task_id,
            "status": status.value,
            "strategy": strategy,
            "retry_count": self._retry_counts[task_id],
            "retried_at": datetime.now(timezone.utc).isoformat(),
            "operator": operator,
        }

        logger.info(
            "任务 '%s' 重试中 (策略: %s, 重试: %d/%d, 操作者: %s)",
            task_id,
            strategy,
            self._retry_counts[task_id],
            self.max_retry_count,
            operator,
        )

        return self._recovery_status[task_id]

    # ==================== 状态查询 ====================

    def get_recovery_status(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """获取任务的恢复状态

        Args:
            task_id: 任务标识

        Returns:
            dict: 恢复状态信息，任务无恢复记录时返回默认状态
        """
        status = self._recovery_status.get(task_id)
        if not status:
            return {
                "task_id": task_id,
                "status": RecoveryStatus.PENDING.value,
                "retry_count": 0,
                "max_retry_count": self.max_retry_count,
                "has_strategy": task_id in self.recovery_strategies,
            }

        return {
            **status,
            "max_retry_count": self.max_retry_count,
            "has_strategy": task_id in self.recovery_strategies,
        }
