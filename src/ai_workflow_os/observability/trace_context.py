"""
追踪上下文传播模块

提供统一的追踪上下文管理，支持跨模块、跨步骤的上下文传播。
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class TraceContext:
    """追踪上下文

    管理链路追踪的上下文信息，支持在Agent、工作流、工具调用等
    各模块之间传递追踪标识，实现端到端的链路串联。
    """

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: str | None = None
    tenant_id: str | None = None
    project_id: str | None = None
    agent_id: str | None = None
    workflow_id: str | None = None
    pipeline_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        """将追踪上下文序列化为字典

        Returns:
            包含所有非空字段的字典，键值均为字符串
        """
        result: dict[str, str] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }

        # 仅序列化非空的可选字段
        optional_fields = (
            "parent_span_id",
            "tenant_id",
            "project_id",
            "agent_id",
            "workflow_id",
            "pipeline_id",
        )
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "TraceContext":
        """从字典反序列化追踪上下文

        Args:
            data: 包含追踪上下文字段的字典

        Returns:
            追踪上下文实例
        """
        return cls(
            trace_id=data.get("trace_id", uuid.uuid4().hex),
            span_id=data.get("span_id", uuid.uuid4().hex[:16]),
            parent_span_id=data.get("parent_span_id"),
            tenant_id=data.get("tenant_id"),
            project_id=data.get("project_id"),
            agent_id=data.get("agent_id"),
            workflow_id=data.get("workflow_id"),
            pipeline_id=data.get("pipeline_id"),
        )

    def child(self, span_id: str) -> "TraceContext":
        """创建子级追踪上下文

        继承当前上下文的trace_id和业务标识，将当前span_id设为
        父级span_id，并使用新的span_id标识子级操作。

        Args:
            span_id: 子级Span的标识

        Returns:
            子级追踪上下文实例
        """
        return TraceContext(
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=self.span_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            agent_id=self.agent_id,
            workflow_id=self.workflow_id,
            pipeline_id=self.pipeline_id,
        )
