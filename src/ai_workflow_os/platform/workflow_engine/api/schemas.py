"""
工作流引擎请求/响应Schema

定义工作流引擎相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO
from ..domain.enums import (
    EdgeConditionType,
    NodeStatus,
    NodeType,
    WorkflowStatus,
)

# =============================================================================
# 节点Schema
# =============================================================================


class WorkflowNodeRequest(BaseModel):
    """工作流节点请求"""

    node_type: NodeType = Field(description="节点类型")
    name: str = Field(description="节点名称")
    config: dict[str, Any] = Field(default_factory=dict, description="节点配置")
    position_x: float = Field(default=0.0, description="前端布局X坐标")
    position_y: float = Field(default=0.0, description="前端布局Y坐标")
    timeout_seconds: int = Field(default=300, ge=1, description="超时时间（秒）")
    retry_count: int = Field(default=0, ge=0, description="重试次数")


class WorkflowNodeResponse(BaseDTO):
    """工作流节点响应"""

    workflow_id: str = Field(description="所属工作流标识")
    node_type: NodeType = Field(description="节点类型")
    name: str = Field(description="节点名称")
    config: dict[str, Any] = Field(description="节点配置")
    position_x: float = Field(description="前端布局X坐标")
    position_y: float = Field(description="前端布局Y坐标")
    timeout_seconds: int = Field(description="超时时间（秒）")
    retry_count: int = Field(description="重试次数")
    status: NodeStatus = Field(description="节点状态")
    started_at: datetime | None = Field(default=None, description="开始执行时间")
    completed_at: datetime | None = Field(default=None, description="完成执行时间")
    error_message: str | None = Field(default=None, description="错误信息")
    duration_ms: float | None = Field(default=None, description="执行时长（毫秒）")


# =============================================================================
# 边Schema
# =============================================================================


class WorkflowEdgeRequest(BaseModel):
    """工作流边请求"""

    source_node_id: str = Field(description="源节点标识")
    target_node_id: str = Field(description="目标节点标识")
    condition_type: EdgeConditionType = Field(default=EdgeConditionType.ALWAYS, description="条件类型")
    condition_expression: str | None = Field(default=None, description="条件表达式")
    priority: int = Field(default=0, description="优先级")


class WorkflowEdgeResponse(BaseDTO):
    """工作流边响应"""

    workflow_id: str = Field(description="所属工作流标识")
    source_node_id: str = Field(description="源节点标识")
    target_node_id: str = Field(description="目标节点标识")
    condition_type: EdgeConditionType = Field(description="条件类型")
    condition_expression: str | None = Field(default=None, description="条件表达式")
    priority: int = Field(description="优先级")


# =============================================================================
# 请求Schema
# =============================================================================


class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""

    name: str = Field(description="工作流名称")
    description: str = Field(default="", description="工作流描述")
    nodes: list[WorkflowNodeRequest] = Field(default_factory=list, description="节点列表")
    edges: list[WorkflowEdgeRequest] = Field(default_factory=list, description="边列表")
    variables: dict[str, Any] = Field(default_factory=dict, description="全局变量")
    workflow_version: str = Field(default="1.0.0", description="工作流版本号")
    operator: str | None = Field(default=None, description="操作者标识")
    tenant_id: str | None = Field(default=None, description="租户标识")


class StartExecutionRequest(BaseModel):
    """启动执行请求"""

    input_data: dict[str, Any] = Field(default_factory=dict, description="执行输入数据")
    operator: str | None = Field(default=None, description="操作者标识")


class ExecuteNodeRequest(BaseModel):
    """执行节点请求"""

    node_id: str = Field(description="节点标识")
    result_data: dict[str, Any] = Field(default_factory=dict, description="节点执行结果数据")
    operator: str | None = Field(default=None, description="操作者标识")


class AdvanceExecutionRequest(BaseModel):
    """推进执行请求"""

    operator: str | None = Field(default=None, description="操作者标识")


# =============================================================================
# 响应Schema
# =============================================================================


class WorkflowDefinitionResponse(BaseDTO):
    """工作流定义响应"""

    name: str = Field(description="工作流名称")
    description: str = Field(description="工作流描述")
    status: WorkflowStatus = Field(description="工作流状态")
    nodes: list[WorkflowNodeResponse] = Field(description="节点列表")
    edges: list[WorkflowEdgeResponse] = Field(description="边列表")
    variables: dict[str, Any] = Field(description="全局变量")
    workflow_version: str = Field(description="工作流版本号")


class WorkflowExecutionResponse(BaseDTO):
    """工作流执行响应"""

    workflow_id: str = Field(description="关联的工作流标识")
    status: WorkflowStatus = Field(description="执行状态")
    current_node_id: str | None = Field(default=None, description="当前执行节点标识")
    node_states: dict[str, NodeStatus] = Field(description="节点状态映射")
    input_data: dict[str, Any] = Field(description="执行输入数据")
    output_data: dict[str, Any] = Field(description="执行输出数据")
    started_at: datetime = Field(description="开始执行时间")
    completed_at: datetime | None = Field(default=None, description="完成执行时间")
    error_message: str | None = Field(default=None, description="错误信息")
    duration_ms: float | None = Field(default=None, description="执行总时长（毫秒）")
    completed_node_count: int = Field(description="已完成节点数")
    failed_node_count: int = Field(description="失败节点数")


class WorkflowListResponse(BaseModel):
    """工作流定义列表响应"""

    items: list[WorkflowDefinitionResponse] = Field(description="工作流定义列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class ExecutionListResponse(BaseModel):
    """执行记录列表响应"""

    items: list[WorkflowExecutionResponse] = Field(description="执行记录列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
