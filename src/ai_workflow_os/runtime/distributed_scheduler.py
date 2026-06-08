"""
分布式调度器模块

实现分布式集群的节点管理与任务调度，支持：
- 节点注册与注销
- Leader 选举
- 任务分配与再平衡
- 心跳检测与健康检查
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 分布式调度器 ====================

class DistributedScheduler:
    """分布式调度器

    管理分布式集群中的节点注册、Leader 选举、任务分配与再平衡。

    Attributes:
        node_id: 当前节点标识
        nodes: 节点信息映射，键为 node_id
        task_queue: 待分配任务队列
        is_leader: 当前节点是否为 Leader
        heartbeat_interval_seconds: 心跳间隔（秒）
        last_heartbeat: 最后一次心跳时间
    """

    def __init__(
        self,
        node_id: str,
        heartbeat_interval_seconds: int = 30,
    ) -> None:
        """初始化分布式调度器

        Args:
            node_id: 当前节点标识
            heartbeat_interval_seconds: 心跳间隔（秒）
        """
        self.node_id: str = node_id
        self.nodes: dict[str, dict[str, Any]] = {}
        self.task_queue: list[dict[str, Any]] = []
        self.is_leader: bool = False
        self.heartbeat_interval_seconds: int = heartbeat_interval_seconds
        self.last_heartbeat: datetime = datetime.now(timezone.utc)
        logger.info(
            "分布式调度器已初始化 (节点: %s, 心跳间隔: %ds)",
            node_id,
            heartbeat_interval_seconds,
        )

    # ==================== 节点管理 ====================

    def register_node(
        self,
        node_id: str,
        node_info: dict[str, Any],
        operator: Optional[str] = None,
    ) -> None:
        """注册节点到集群

        Args:
            node_id: 节点标识
            node_info: 节点信息（包含 host、port、capabilities 等）
            operator: 操作者标识
        """
        if node_id in self.nodes:
            logger.warning("节点 '%s' 已存在于集群中，将更新其信息", node_id)

        self.nodes[node_id] = {
            **node_info,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "registered_by": operator,
            "is_alive": True,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("已注册节点: %s (操作者: %s)", node_id, operator)

        # 首个节点注册时自动成为 Leader
        if len(self.nodes) == 1 and node_id == self.node_id:
            self.is_leader = True
            logger.info("节点 '%s' 成为 Leader（首个注册节点）", node_id)

    def deregister_node(
        self,
        node_id: str,
        operator: Optional[str] = None,
    ) -> None:
        """从集群注销节点

        Args:
            node_id: 节点标识
            operator: 操作者标识
        """
        if node_id not in self.nodes:
            logger.warning("节点 '%s' 不存在于集群中，无法注销", node_id)
            return

        del self.nodes[node_id]
        logger.info("已注销节点: %s (操作者: %s)", node_id, operator)

        # 如果注销的是 Leader，触发重新选举
        if node_id == self.node_id and self.is_leader:
            self.is_leader = False
            new_leader = self.elect_leader()
            logger.info("原 Leader 已注销，新 Leader 为: %s", new_leader)

    # ==================== Leader 选举 ====================

    def elect_leader(self) -> str:
        """选举 Leader 节点

        基于节点 ID 字典序选择第一个存活节点作为 Leader。

        Returns:
            str: 新选出的 Leader 节点 ID

        Raises:
            RuntimeError: 当集群中没有存活节点时抛出
        """
        alive_nodes = [
            node_id
            for node_id, info in self.nodes.items()
            if info.get("is_alive", False)
        ]

        if not alive_nodes:
            raise RuntimeError("集群中没有存活的节点，无法选举 Leader")

        # 按节点 ID 字典序选举
        alive_nodes.sort()
        new_leader = alive_nodes[0]

        # 更新 Leader 状态
        if new_leader == self.node_id:
            self.is_leader = True
        else:
            self.is_leader = False

        logger.info("Leader 选举完成: %s", new_leader)
        return new_leader

    # ==================== 任务分配 ====================

    def assign_task(
        self,
        task: dict[str, Any],
        operator: Optional[str] = None,
    ) -> dict[str, str]:
        """分配任务到合适的节点

        将任务分配给负载最低的存活节点。

        Args:
            task: 任务信息
            operator: 操作者标识

        Returns:
            dict: 分配结果，包含 task_id 和 assigned_node

        Raises:
            RuntimeError: 当没有可用节点时抛出
        """
        alive_nodes = {
            node_id: info
            for node_id, info in self.nodes.items()
            if info.get("is_alive", False)
        }

        if not alive_nodes:
            raise RuntimeError("没有可用的存活节点来分配任务")

        # 选择负载最低的节点（按 task_count 排序）
        selected_node = min(
            alive_nodes.items(),
            key=lambda item: item[1].get("task_count", 0),
        )
        selected_node_id = selected_node[0]

        # 更新节点任务计数
        self.nodes[selected_node_id]["task_count"] = (
            self.nodes[selected_node_id].get("task_count", 0) + 1
        )

        task_id = task.get("task_id", "")
        logger.info(
            "任务 '%s' 已分配至节点 '%s' (操作者: %s)",
            task_id,
            selected_node_id,
            operator,
        )

        return {
            "task_id": task_id,
            "assigned_node": selected_node_id,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "assigned_by": operator,
        }

    def rebalance_tasks(
        self,
        operator: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """重新平衡任务分配

        将队列中的待分配任务均匀分配到所有存活节点。

        Args:
            operator: 操作者标识

        Returns:
            list: 任务重新分配结果列表
        """
        alive_nodes = [
            node_id
            for node_id, info in self.nodes.items()
            if info.get("is_alive", False)
        ]

        if not alive_nodes:
            logger.warning("没有可用节点，任务再平衡跳过")
            return []

        results: list[dict[str, str]] = []
        node_index = 0

        for task in self.task_queue:
            selected_node = alive_nodes[node_index % len(alive_nodes)]
            results.append({
                "task_id": task.get("task_id", ""),
                "reassigned_node": selected_node,
                "reassigned_at": datetime.now(timezone.utc).isoformat(),
                "reassigned_by": operator,
            })
            node_index += 1

        self.task_queue.clear()
        logger.info(
            "任务再平衡完成: %d 个任务已分配 (操作者: %s)",
            len(results),
            operator,
        )

        return results

    # ==================== 集群状态 ====================

    def get_cluster_status(self) -> dict[str, Any]:
        """获取集群状态

        Returns:
            dict: 集群状态信息，包括节点列表、Leader 信息和任务队列长度
        """
        alive_count = sum(
            1 for info in self.nodes.values() if info.get("is_alive", False)
        )

        return {
            "current_node": self.node_id,
            "is_leader": self.is_leader,
            "total_nodes": len(self.nodes),
            "alive_nodes": alive_count,
            "pending_tasks": len(self.task_queue),
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "nodes": {
                node_id: {
                    "is_alive": info.get("is_alive", False),
                    "task_count": info.get("task_count", 0),
                    "last_heartbeat": info.get("last_heartbeat", ""),
                }
                for node_id, info in self.nodes.items()
            },
        }

    # ==================== 心跳管理 ====================

    def send_heartbeat(
        self,
        node_id: str,
        operator: Optional[str] = None,
    ) -> None:
        """发送心跳

        更新指定节点的最后心跳时间。

        Args:
            node_id: 节点标识
            operator: 操作者标识
        """
        if node_id not in self.nodes:
            logger.warning("节点 '%s' 不存在，无法发送心跳", node_id)
            return

        now = datetime.now(timezone.utc)
        self.nodes[node_id]["last_heartbeat"] = now.isoformat()
        self.nodes[node_id]["is_alive"] = True

        if node_id == self.node_id:
            self.last_heartbeat = now

        logger.debug("心跳已发送至节点: %s (操作者: %s)", node_id, operator)

    def check_node_health(self) -> list[str]:
        """检查节点健康状态

        检测所有节点的心跳超时情况，将超时节点标记为不存活。

        Returns:
            list: 不健康的节点 ID 列表
        """
        now = datetime.now(timezone.utc)
        unhealthy_nodes: list[str] = []
        timeout_seconds = self.heartbeat_interval_seconds * 3

        for node_id, info in self.nodes.items():
            last_heartbeat_str = info.get("last_heartbeat", "")
            if not last_heartbeat_str:
                unhealthy_nodes.append(node_id)
                info["is_alive"] = False
                continue

            try:
                last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                elapsed = (now - last_heartbeat).total_seconds()
                if elapsed > timeout_seconds:
                    unhealthy_nodes.append(node_id)
                    info["is_alive"] = False
                    logger.warning(
                        "节点 '%s' 心跳超时 (%.1fs > %ds)",
                        node_id,
                        elapsed,
                        timeout_seconds,
                    )
            except (ValueError, TypeError):
                unhealthy_nodes.append(node_id)
                info["is_alive"] = False
                logger.warning("节点 '%s' 心跳时间格式异常", node_id)

        if unhealthy_nodes:
            logger.warning("发现不健康节点: %s", unhealthy_nodes)

        return unhealthy_nodes
