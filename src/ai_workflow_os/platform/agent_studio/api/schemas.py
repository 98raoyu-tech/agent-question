"""
Agent Studio请求/响应Schema

定义Agent相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO, UpdateDTO
from ..domain.enums import AgentStatus, AgentType


# =============================================================================
# 模型配置Schema
# =============================================================================


class ModelConfigSchema(BaseModel):
    """模型配置Schema"""

    model_name: str = Field(default="gpt-4", description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, description="最大token数")
    top_p: float = Field(default=1.0, ge=0, le=1, description="Top-P采样参数")
    extra_params: dict[str, Any] = Field(default_factory=dict, description="额外模型参数")


class ToolConfigSchema(BaseModel):
    """工具配置Schema"""

    tool_id: str = Field(description="工具标识")
    tool_name: str = Field(description="工具名称")
    tool_type: str = Field(description="工具类型")
    description: str = Field(default="", description="工具描述")
    parameters: dict[str, Any] = Field(default_factory=dict, description="工具参数定义")
    is_required: bool = Field(default=False, description="是否必需")


class KnowledgeSourceConfigSchema(BaseModel):
    """知识源配置Schema"""

    source_id: str = Field(description="知识源标识")
    source_name: str = Field(description="知识源名称")
    source_type: str = Field(description="知识源类型")
    retrieval_config: dict[str, Any] = Field(default_factory=dict, description="检索配置")
    is_enabled: bool = Field(default=True, description="是否启用")


# =============================================================================
# 请求Schema
# =============================================================================


class CreateAgentRequest(CreateDTO):
    """创建Agent请求"""

    name: str = Field(min_length=1, max_length=200, description="Agent名称")
    description: str = Field(default="", max_length=2000, description="Agent描述")
    agent_type: AgentType = Field(default=AgentType.SINGLE, description="Agent类型")
    system_prompt: str = Field(default="", description="系统提示词")
    llm_config: ModelConfigSchema = Field(default_factory=ModelConfigSchema, description="模型配置")
    tools: list[ToolConfigSchema] = Field(default_factory=list, description="工具列表")
    knowledge_sources: list[KnowledgeSourceConfigSchema] = Field(
        default_factory=list, description="知识源列表"
    )
    tags: list[str] = Field(default_factory=list, description="标签列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class UpdateAgentRequest(UpdateDTO):
    """更新Agent请求"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Agent名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="Agent描述")
    agent_type: Optional[AgentType] = Field(default=None, description="Agent类型")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    llm_config: Optional[ModelConfigSchema] = Field(default=None, description="模型配置")
    tools: Optional[list[ToolConfigSchema]] = Field(default=None, description="工具列表")
    knowledge_sources: Optional[list[KnowledgeSourceConfigSchema]] = Field(
        default=None, description="知识源列表"
    )
    tags: Optional[list[str]] = Field(default=None, description="标签列表")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="扩展元数据")


class PublishAgentRequest(BaseModel):
    """发布Agent请求"""

    release_name: str = Field(default="", description="发布名称")
    release_notes: str = Field(default="", description="发布说明")


# =============================================================================
# 响应Schema
# =============================================================================


class ModelConfigResponse(BaseModel):
    """模型配置响应"""

    model_name: str = Field(description="模型名称")
    temperature: float = Field(description="温度参数")
    max_tokens: int = Field(description="最大token数")
    top_p: float = Field(description="Top-P采样参数")


class AgentResponse(BaseDTO):
    """Agent响应"""

    name: str = Field(description="Agent名称")
    description: str = Field(description="Agent描述")
    agent_type: AgentType = Field(description="Agent类型")
    status: AgentStatus = Field(description="Agent状态")
    system_prompt: str = Field(description="系统提示词")
    llm_config: ModelConfigResponse = Field(description="模型配置")
    tools: list[ToolConfigSchema] = Field(description="工具列表")
    knowledge_sources: list[KnowledgeSourceConfigSchema] = Field(description="知识源列表")
    tags: list[str] = Field(description="标签列表")


class AgentListResponse(BaseModel):
    """Agent列表响应"""

    items: list[AgentResponse] = Field(description="Agent列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


class AgentVersionResponse(BaseDTO):
    """Agent版本响应"""

    agent_id: str = Field(description="Agent标识")
    version_number: str = Field(description="版本号")
    change_log: str = Field(description="变更日志")
    is_current: bool = Field(description="是否为当前版本")


class AgentReleaseResponse(BaseDTO):
    """Agent发布响应"""

    agent_id: str = Field(description="Agent标识")
    version_id: str = Field(description="版本标识")
    release_name: str = Field(description="发布名称")
    status: str = Field(description="发布状态")
    release_notes: str = Field(description="发布说明")
    rollout_percentage: int = Field(description="灰度百分比")
    released_at: Optional[datetime] = Field(default=None, description="发布时间")
