"""
心跳管理模块

实现分布式集群节点的心跳监控，支持：
- 节点注册与注销
- 心跳信号发送
- 全局健康检查
- 节点存活状态查询
- 节点运行时长统计
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 心跳管理器 ====================

class HeartbeatManager:
    """心跳管理器

    监控分布式集群中各节点的心跳状态，检测节点存活情况，
    并在节点失联时触发回调通知。

    Attributes:
        nodes: 节点心跳信息映射，键为 node_id
        heartbeat_interval: 心跳发送间隔（秒）
        timeout_threshold: 心跳超时阈值（秒）
        on_failure_callback: 节点失联时的回调函数
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        timeout_threshold: int = 90,
        on_failure_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """初始化心跳管理器

        Args:
            heartbeat_interval: 心跳发送间隔（秒）
            timeout_threshold: 心跳超时阈值（秒），超过此时间未收到心跳则判定节点失联
            on_failure_callback: 节点失联时的回调函数，参数为 node_id
        """
        self.nodes: dict[str, dict[str, Any]] = {}
        self.heartbeat_interval: int = heartbeat_interval
        self.timeout_threshold: int = timeout_threshold
        self.on_failure_callback: Optional[Callable[[str], None]] = on_failure_callback
        logger.info(
            "心跳管理器已初始化 (间隔: %ds, 超时阈值: %ds)",
            heartbeat_interval,
            timeout_threshold,
        )

    # ==================== 节点注册 ====================

    def register(
        self,
        node_id: str,
        config: dict[str, Any],
    ) -> None:
        """注册节点

        Args:
            node_id: 节点标识
            config: 节点配置信息（包含 host、port、role 等）
        """
        if node_id in self.nodes:
            logger.warning("节点 '%s' 已注册，将更新其配置", node_id)

        now = time.time()
        self.nodes[node_id] = {
            **config,
            "registered_at": now,
            "last_heartbeat": now,
            "is_alive": True,
            "beat_count": 0,
        }

        logger.info("已注册节点: %s", node_id)

    def unregister(self, node_id: str) -> None:
        """注销节点

        Args:
            node_id: 节点标识
        """
        if node_id not in self.nodes:
            logger.warning("节点 '%s' 不存在，无法注销", node_id)
            return

        del self.nodes[node_id]
        logger.info("已注销节点: %s", node_id)

    # ==================== 心跳信号 ====================

    def beat(self, node_id: str) -> None:
        """发送心跳

        更新指定节点的最后心跳时间和心跳计数。

        Args:
            node_id: 节点标识
        """
        if node_id not in self.nodes:
            logger.warning("节点 '%s' 未注册，无法发送心跳", node_id)
            return

        now = time.time()
        node = self.nodes[node_id]
        node["last_heartbeat"] = now
        node["is_alive"] = True
        node["beat_count"] = node.get("beat_count", 0) + 1

        logger.debug(
            "节点 '%s' 心跳 #%d 已记录",
            node_id,
            node["beat_count"],
        )

    # ==================== 健康检查 ====================

    def check_all(self) -> list[str]:
        """检查所有节点的健康状态

        遍历所有已注册节点，检测心跳超时情况。
        超时的节点将被标记为不存活，并触发失败回调。

        Returns:
            list: 失联节点的 node_id 列表
        """
        now = time.time()
        dead_nodes: list[str] = []

        for node_id, node in self.nodes.items():
            elapsed = now - node.get("last_heartbeat", 0)

            if elapsed > self.timeout_threshold:
                if node.get("is_alive", False):
                    node["is_alive"] = False
                    dead_nodes.append(node_id)
                    logger.warning(
                        "节点 '%s' 心跳超时 (%.1fs > %ds)",
                        node_id,
                        elapsed,
                        self.timeout_threshold,
                    )

                    # 触发失败回调
                    if self.on_failure_callback:
                        try:
                            self.on_failure_callback(node_id)
                        except Exception as error:
                            logger.error(
                                "节点 '%s' 失败回调执行异常: %s - %s",
                                node_id,
                                type(error).__name__,
                                str(error),
                            )

        if dead_nodes:
            logger.warning("检测到失联节点: %s", dead_nodes)

        return dead_nodes

    # ==================== 状态查询 ====================

    def is_alive(self, node_id: str) -> bool:
        """查询节点是否存活

        Args:
            node_id: 节点标识

        Returns:
            bool: 节点存活返回 True，不存在或失联返回 False
        """
        node = self.nodes.get(node_id)
        if not node:
            logger.debug("节点 '%s' 未注册", node_id)
            return False

        return node.get("is_alive", False)

    def get_node_uptime(self, node_id: str) -> float:
        """获取节点运行时长

        从节点注册时间开始计算到当前的持续时长。

        Args:
            node_id: 节点标识

        Returns:
            float: 运行时长（秒），节点不存在返回 0.0
        """
        node = self.nodes.get(node_id)
        if not node:
            logger.warning("节点 '%s' 不存在，无法获取运行时长", node_id)
            return 0.0

        registered_at = node.get("registered_at", 0)
        if registered_at <= 0:
            return 0.0

        uptime = time.time() - registered_at
        return round(uptime, 2)
