"""
故障转移模块

实现分布式集群的主备切换与故障恢复，支持：
- 主动故障转移（手动触发）
- 自动故障转移检测
- 主节点恢复
- 备用节点管理
- 故障转移历史记录
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class FailoverStatus(str, Enum):
    """故障转移状态枚举"""
    NORMAL = "normal"
    FAILOVER = "failover"
    RECOVERY = "recovery"


# ==================== 故障转移管理器 ====================

class FailoverManager:
    """故障转移管理器

    管理分布式集群的主备切换，支持手动触发故障转移、
    自动检测和主节点恢复。

    Attributes:
        primary_node_id: 主节点标识
        standby_nodes: 备用节点标识列表
        current_active: 当前活跃节点标识
        failover_status: 故障转移状态
        last_failover_at: 最后一次故障转移时间
        failover_history: 故障转移历史记录
    """

    def __init__(
        self,
        primary_node_id: str,
        standby_nodes: Optional[list[str]] = None,
    ) -> None:
        """初始化故障转移管理器

        Args:
            primary_node_id: 主节点标识
            standby_nodes: 备用节点标识列表
        """
        self.primary_node_id: str = primary_node_id
        self.standby_nodes: list[str] = standby_nodes or []
        self.current_active: str = primary_node_id
        self.failover_status: FailoverStatus = FailoverStatus.NORMAL
        self.last_failover_at: Optional[datetime] = None
        self.failover_history: list[dict[str, Any]] = []
        logger.info(
            "故障转移管理器已初始化 (主节点: %s, 备用节点数: %d)",
            primary_node_id,
            len(self.standby_nodes),
        )

    # ==================== 故障转移 ====================

    def trigger_failover(
        self,
        reason: str,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """触发故障转移

        将活跃节点从当前主节点切换到第一个可用的备用节点。

        Args:
            reason: 故障转移原因
            operator: 操作者标识

        Returns:
            dict: 故障转移结果

        Raises:
            RuntimeError: 当没有可用的备用节点时抛出
        """
        if not self.standby_nodes:
            raise RuntimeError("没有可用的备用节点，无法执行故障转移")

        now = datetime.now(timezone.utc)
        previous_active = self.current_active

        # 选择第一个备用节点作为新的活跃节点
        new_active = self.standby_nodes[0]

        # 更新状态
        self.current_active = new_active
        self.failover_status = FailoverStatus.FAILOVER
        self.last_failover_at = now

        # 记录历史
        history_entry = {
            "timestamp": now.isoformat(),
            "from_node": previous_active,
            "to_node": new_active,
            "reason": reason,
            "operator": operator,
            "type": "failover",
        }
        self.failover_history.append(history_entry)

        logger.warning(
            "故障转移已触发: %s -> %s (原因: %s, 操作者: %s)",
            previous_active,
            new_active,
            reason,
            operator,
        )

        return {
            "previous_active": previous_active,
            "new_active": new_active,
            "failover_status": self.failover_status.value,
            "timestamp": now.isoformat(),
            "reason": reason,
        }

    # ==================== 恢复 ====================

    def recover(
        self,
        primary_node_id: str,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """恢复主节点

        将活跃节点切换回指定的主节点。

        Args:
            primary_node_id: 要恢复的主节点标识
            operator: 操作者标识

        Returns:
            dict: 恢复结果
        """
        now = datetime.now(timezone.utc)
        previous_active = self.current_active

        # 更新状态
        self.primary_node_id = primary_node_id
        self.current_active = primary_node_id
        self.failover_status = FailoverStatus.RECOVERY

        # 将之前的主节点从备用列表移除（如果存在）
        if primary_node_id in self.standby_nodes:
            self.standby_nodes.remove(primary_node_id)

        # 将之前的活跃节点加入备用列表
        if (
            previous_active != primary_node_id
            and previous_active not in self.standby_nodes
        ):
            self.standby_nodes.append(previous_active)

        # 记录历史
        history_entry = {
            "timestamp": now.isoformat(),
            "from_node": previous_active,
            "to_node": primary_node_id,
            "reason": "recovery",
            "operator": operator,
            "type": "recovery",
        }
        self.failover_history.append(history_entry)

        logger.info(
            "主节点已恢复: %s -> %s (操作者: %s)",
            previous_active,
            primary_node_id,
            operator,
        )

        # 恢复完成后切换到正常状态
        self.failover_status = FailoverStatus.NORMAL

        return {
            "previous_active": previous_active,
            "restored_primary": primary_node_id,
            "failover_status": self.failover_status.value,
            "timestamp": now.isoformat(),
        }

    # ==================== 状态查询 ====================

    def get_status(self) -> dict[str, Any]:
        """获取故障转移状态

        Returns:
            dict: 当前故障转移状态信息
        """
        return {
            "primary_node_id": self.primary_node_id,
            "current_active": self.current_active,
            "failover_status": self.failover_status.value,
            "standby_nodes": self.standby_nodes.copy(),
            "last_failover_at": (
                self.last_failover_at.isoformat()
                if self.last_failover_at
                else None
            ),
            "history_count": len(self.failover_history),
            "is_in_failover": self.failover_status == FailoverStatus.FAILOVER,
        }

    # ==================== 备用节点管理 ====================

    def add_standby(
        self,
        node_id: str,
        operator: Optional[str] = None,
    ) -> None:
        """添加备用节点

        Args:
            node_id: 备用节点标识
            operator: 操作者标识
        """
        if node_id in self.standby_nodes:
            logger.warning("节点 '%s' 已在备用节点列表中", node_id)
            return

        if node_id == self.current_active:
            logger.warning("节点 '%s' 是当前活跃节点，不能添加为备用节点", node_id)
            return

        self.standby_nodes.append(node_id)
        logger.info(
            "已添加备用节点: %s (当前备用节点数: %d, 操作者: %s)",
            node_id,
            len(self.standby_nodes),
            operator,
        )

    def remove_standby(
        self,
        node_id: str,
        operator: Optional[str] = None,
    ) -> bool:
        """移除备用节点

        Args:
            node_id: 备用节点标识
            operator: 操作者标识

        Returns:
            bool: 移除成功返回 True，节点不存在返回 False
        """
        if node_id not in self.standby_nodes:
            logger.warning("节点 '%s' 不在备用节点列表中", node_id)
            return False

        self.standby_nodes.remove(node_id)
        logger.info(
            "已移除备用节点: %s (当前备用节点数: %d, 操作者: %s)",
            node_id,
            len(self.standby_nodes),
            operator,
        )

        return True

    # ==================== 自动检测 ====================

    def auto_failover_check(self) -> bool:
        """自动故障转移检测

        检查当前是否处于故障转移状态。
        此方法供外部监控系统调用，判断是否需要执行自动故障转移。

        Returns:
            bool: 当前处于故障转移状态返回 True（表示已发生故障转移）
        """
        is_in_failover = self.failover_status == FailoverStatus.FAILOVER

        if is_in_failover:
            logger.debug("当前处于故障转移状态")

        return is_in_failover
