"""
领域指标收集模块

提供面向业务领域的指标收集能力，支持Agent、工作流、工具调用
和成本等维度的指标记录与查询。
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MetricEntry:
    """指标条目

    Attributes:
        name: 指标名称
        value: 指标值
        tags: 标签字典，用于多维度分类
        timestamp: 记录时间戳
    """

    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """领域指标收集器

    面向业务领域提供Agent、工作流、工具调用和成本等维度的指标收集，
    内部使用MetricEntry列表存储，支持按名称、标签和时间范围查询。
    """

    def __init__(self) -> None:
        """初始化指标收集器"""
        self._entries: list[MetricEntry] = []

    def record_agent_metric(
        self,
        agent_id: str,
        metric_name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """记录Agent指标

        Args:
            agent_id: Agent标识
            metric_name: 指标名称
            value: 指标值
            tags: 额外标签
        """
        merged_tags = {"agent_id": agent_id, **(tags or {})}
        entry = MetricEntry(name=metric_name, value=value, tags=merged_tags)
        self._entries.append(entry)
        logger.debug(f"Agent指标已记录: {metric_name}={value}, agent_id={agent_id}")

    def record_workflow_metric(
        self,
        workflow_id: str,
        metric_name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """记录工作流指标

        Args:
            workflow_id: 工作流标识
            metric_name: 指标名称
            value: 指标值
            tags: 额外标签
        """
        merged_tags = {"workflow_id": workflow_id, **(tags or {})}
        entry = MetricEntry(name=metric_name, value=value, tags=merged_tags)
        self._entries.append(entry)
        logger.debug(f"工作流指标已记录: {metric_name}={value}, workflow_id={workflow_id}")

    def record_tool_metric(
        self,
        tool_id: str,
        metric_name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """记录工具指标

        Args:
            tool_id: 工具标识
            metric_name: 指标名称
            value: 指标值
            tags: 额外标签
        """
        merged_tags = {"tool_id": tool_id, **(tags or {})}
        entry = MetricEntry(name=metric_name, value=value, tags=merged_tags)
        self._entries.append(entry)
        logger.debug(f"工具指标已记录: {metric_name}={value}, tool_id={tool_id}")

    def record_cost_metric(
        self,
        agent_id: str,
        cost_type: str,
        amount: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """记录成本指标

        Args:
            agent_id: Agent标识
            cost_type: 成本类型（如 llm_tokens、api_calls）
            amount: 金额
            tags: 额外标签
        """
        merged_tags = {
            "agent_id": agent_id,
            "cost_type": cost_type,
            **(tags or {}),
        }
        entry = MetricEntry(name="cost", value=amount, tags=merged_tags)
        self._entries.append(entry)
        logger.debug(
            f"成本指标已记录: {cost_type}={amount}, agent_id={agent_id}"
        )

    def get_metrics(
        self,
        name: str | None = None,
        tags: dict[str, str] | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[dict]:
        """查询指标

        按名称、标签和时间范围过滤指标记录。所有过滤条件之间为AND关系。

        Args:
            name: 指标名称，为None时不按名称过滤
            tags: 标签过滤条件，要求记录的标签包含所有指定键值对
            start_time: 起始时间戳（含），为None时不设下限
            end_time: 结束时间戳（含），为None时不设上限

        Returns:
            满足条件的指标字典列表
        """
        results: list[dict] = []

        for entry in self._entries:
            # 按名称过滤
            if name is not None and entry.name != name:
                continue

            # 按时间范围过滤
            if start_time is not None and entry.timestamp < start_time:
                continue
            if end_time is not None and entry.timestamp > end_time:
                continue

            # 按标签过滤：要求记录包含所有指定的标签键值对
            if tags is not None:
                if not self._tags_match(entry.tags, tags):
                    continue

            results.append({
                "name": entry.name,
                "value": entry.value,
                "tags": entry.tags,
                "timestamp": entry.timestamp,
            })

        return results

    @staticmethod
    def _tags_match(
        entry_tags: dict[str, str],
        filter_tags: dict[str, str],
    ) -> bool:
        """检查指标标签是否满足过滤条件

        Args:
            entry_tags: 指标记录的标签
            filter_tags: 过滤条件标签

        Returns:
            记录标签包含所有过滤条件键值对时返回True
        """
        for key, value in filter_tags.items():
            if entry_tags.get(key) != value:
                return False
        return True

    def clear(self) -> None:
        """清空所有指标记录"""
        self._entries.clear()
        logger.info("领域指标已全部清空")


# 全局领域指标收集器实例
domain_metrics_collector = MetricsCollector()
