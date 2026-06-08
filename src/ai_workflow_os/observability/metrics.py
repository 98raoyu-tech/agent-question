"""
指标收集模块

收集和导出系统运行指标，支持计数器、仪表盘和直方图。
提供Prometheus格式导出。
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值"""
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """指标收集器"""

    def __init__(self) -> None:
        """初始化指标收集器"""
        self._counters: dict[str, list[MetricValue]] = {}
        self._gauges: dict[str, list[MetricValue]] = {}
        self._histograms: dict[str, list[MetricValue]] = {}

        # 初始化预定义指标
        self._init_predefined_metrics()

    def _init_predefined_metrics(self) -> None:
        """初始化预定义指标"""
        # Agent任务总数
        self._counters["agent_tasks_total"] = []
        # 工作流执行总数
        self._counters["workflow_executions_total"] = []
        # 工具调用总数
        self._counters["tool_invocations_total"] = []
        # 记忆操作总数
        self._counters["memory_operations_total"] = []
        # LLM token使用总量
        self._counters["llm_tokens_used_total"] = []
        # 请求持续时间
        self._histograms["request_duration_seconds"] = []

    def increment_counter(
        self,
        name: str,
        value: float = 1,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """递增计数器

        Args:
            name: 计数器名称
            value: 递增值
            labels: 标签字典
        """
        if name not in self._counters:
            self._counters[name] = []

        metric = MetricValue(
            value=value,
            labels=labels or {},
        )
        self._counters[name].append(metric)

        logger.debug(f"计数器递增: {name} += {value}, 标签={labels}")

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """设置仪表盘值

        Args:
            name: 仪表盘名称
            value: 设置的值
            labels: 标签字典
        """
        if name not in self._gauges:
            self._gauges[name] = []

        # 对于相同标签的指标，替换旧值
        self._gauges[name] = [
            m for m in self._gauges[name]
            if m.labels != (labels or {})
        ]

        metric = MetricValue(
            value=value,
            labels=labels or {},
        )
        self._gauges[name].append(metric)

        logger.debug(f"仪表盘设置: {name} = {value}, 标签={labels}")

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """记录直方图值

        Args:
            name: 直方图名称
            value: 观测值
            labels: 标签字典
        """
        if name not in self._histograms:
            self._histograms[name] = []

        metric = MetricValue(
            value=value,
            labels=labels or {},
        )
        self._histograms[name].append(metric)

        logger.debug(f"直方图记录: {name} += {value}, 标签={labels}")

    def get_metrics(self) -> dict[str, Any]:
        """获取所有指标

        Returns:
            包含所有指标的字典
        """
        def summarize_values(values: list[MetricValue]) -> dict[str, Any]:
            """汇总指标值"""
            if not values:
                return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}

            total = sum(m.value for m in values)
            return {
                "count": len(values),
                "sum": total,
                "min": min(m.value for m in values),
                "max": max(m.value for m in values),
                "avg": total / len(values) if values else 0,
            }

        return {
            "counters": {
                name: summarize_values(values)
                for name, values in self._counters.items()
            },
            "gauges": {
                name: [
                    {"value": m.value, "labels": m.labels}
                    for m in values
                ]
                for name, values in self._gauges.items()
            },
            "histograms": {
                name: summarize_values(values)
                for name, values in self._histograms.items()
            },
        }

    def export_prometheus(self) -> str:
        """导出Prometheus格式的指标

        Returns:
            Prometheus格式的指标字符串
        """
        lines = []

        # 导出计数器
        for name, values in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            if values:
                # 按标签分组汇总
                label_groups: dict[str, float] = {}
                for v in values:
                    label_key = self._format_labels(v.labels)
                    label_groups[label_key] = label_groups.get(label_key, 0) + v.value

                for label_str, total in label_groups.items():
                    if label_str:
                        lines.append(f"{name}{{{label_str}}} {total}")
                    else:
                        lines.append(f"{name} {total}")
            else:
                lines.append(f"{name} 0")

        # 导出仪表盘
        for name, values in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            if values:
                for v in values:
                    label_str = self._format_labels(v.labels)
                    if label_str:
                        lines.append(f"{name}{{{label_str}}} {v.value}")
                    else:
                        lines.append(f"{name} {v.value}")
            else:
                lines.append(f"{name} 0")

        # 导出直方图（简化为sum和count）
        for name, values in self._histograms.items():
            lines.append(f"# TYPE {name} histogram")
            if values:
                total = sum(v.value for v in values)
                count = len(values)
                lines.append(f"{name}_sum {total:.6f}")
                lines.append(f"{name}_count {count}")
            else:
                lines.append(f"{name}_sum 0")
                lines.append(f"{name}_count 0")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_labels(labels: dict[str, str]) -> str:
        """格式化标签为Prometheus格式

        Args:
            labels: 标签字典

        Returns:
            格式化的标签字符串
        """
        if not labels:
            return ""

        formatted = [f'{key}="{value}"' for key, value in sorted(labels.items())]
        return ",".join(formatted)

    def reset(self) -> None:
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._init_predefined_metrics()
        logger.info("指标收集器已重置")

    def record_agent_task(
        self,
        agent_type: str,
        status: str,
    ) -> None:
        """记录Agent任务

        Args:
            agent_type: Agent类型
            status: 任务状态
        """
        self.increment_counter(
            "agent_tasks_total",
            labels={"agent_type": agent_type, "status": status},
        )

    def record_workflow_execution(
        self,
        workflow_id: str,
        status: str,
    ) -> None:
        """记录工作流执行

        Args:
            workflow_id: 工作流ID
            status: 执行状态
        """
        self.increment_counter(
            "workflow_executions_total",
            labels={"workflow_id": workflow_id, "status": status},
        )

    def record_tool_invocation(
        self,
        tool_name: str,
        success: bool,
    ) -> None:
        """记录工具调用

        Args:
            tool_name: 工具名称
            success: 是否成功
        """
        self.increment_counter(
            "tool_invocations_total",
            labels={"tool_name": tool_name, "status": "success" if success else "failure"},
        )

    def record_memory_operation(
        self,
        operation: str,
        memory_type: str,
    ) -> None:
        """记录记忆操作

        Args:
            operation: 操作类型 (store/recall/delete)
            memory_type: 记忆类型
        """
        self.increment_counter(
            "memory_operations_total",
            labels={"operation": operation, "memory_type": memory_type},
        )

    def record_llm_tokens(
        self,
        model: str,
        token_type: str,
        count: int,
    ) -> None:
        """记录LLM token使用

        Args:
            model: 模型名称
            token_type: token类型 (prompt/completion)
            count: token数量
        """
        self.increment_counter(
            "llm_tokens_used_total",
            value=count,
            labels={"model": model, "type": token_type},
        )

    def record_request_duration(
        self,
        method: str,
        path: str,
        duration: float,
    ) -> None:
        """记录请求持续时间

        Args:
            method: HTTP方法
            path: 请求路径
            duration: 持续时间（秒）
        """
        self.observe_histogram(
            "request_duration_seconds",
            value=duration,
            labels={"method": method, "path": path},
        )


# 全局指标收集器实例
metrics_collector = MetricsCollector()
