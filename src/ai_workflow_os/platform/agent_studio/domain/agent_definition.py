"""
Agent定义实体

定义Agent的核心业务实体，包含名称、描述、类型、系统提示词、模型配置、工具和知识源等。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity
from .enums import AgentStatus, AgentType


@dataclass
class ModelConfig:
    """模型配置值对象

    Attributes:
        model_name: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数
        top_p: Top-P采样参数
        extra_params: 额外模型参数
    """

    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfig:
    """工具配置值对象

    Attributes:
        tool_id: 工具标识
        tool_name: 工具名称
        tool_type: 工具类型
        description: 工具描述
        parameters: 工具参数定义
        is_required: 是否必需
    """

    tool_id: str = ""
    tool_name: str = ""
    tool_type: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    is_required: bool = False


@dataclass
class KnowledgeSourceConfig:
    """知识源配置值对象

    Attributes:
        source_id: 知识源标识
        source_name: 知识源名称
        source_type: 知识源类型
        retrieval_config: 检索配置
        is_enabled: 是否启用
    """

    source_id: str = ""
    source_name: str = ""
    source_type: str = ""
    retrieval_config: dict[str, Any] = field(default_factory=dict)
    is_enabled: bool = True


@dataclass
class AgentDefinition(BaseEntity):
    """Agent定义实体

    核心业务实体，描述一个Agent的完整定义。

    Attributes:
        name: Agent名称
        description: Agent描述
        agent_type: Agent类型
        status: Agent状态
        system_prompt: 系统提示词
        model_config: 模型配置
        tools: 工具列表
        knowledge_sources: 知识源列表
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    agent_type: AgentType = AgentType.SINGLE
    status: AgentStatus = AgentStatus.DRAFT
    system_prompt: str = ""
    model_config: ModelConfig = field(default_factory=ModelConfig)
    tools: list[ToolConfig] = field(default_factory=list)
    knowledge_sources: list[KnowledgeSourceConfig] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def publish(self, operator: Optional[str] = None) -> None:
        """发布Agent

        Args:
            operator: 操作者标识
        """
        self.status = AgentStatus.PUBLISHED
        self.touch(operator)

    def archive(self, operator: Optional[str] = None) -> None:
        """归档Agent

        Args:
            operator: 操作者标识
        """
        self.status = AgentStatus.ARCHIVED
        self.touch(operator)

    def deprecate(self, operator: Optional[str] = None) -> None:
        """废弃Agent

        Args:
            operator: 操作者标识
        """
        self.status = AgentStatus.DEPRECATED
        self.touch(operator)

    def add_tool(self, tool_config: ToolConfig, operator: Optional[str] = None) -> None:
        """添加工具配置

        Args:
            tool_config: 工具配置
            operator: 操作者标识
        """
        # 检查工具是否已存在
        existing_ids = [t.tool_id for t in self.tools]
        if tool_config.tool_id not in existing_ids:
            self.tools.append(tool_config)
            self.touch(operator)

    def remove_tool(self, tool_id: str, operator: Optional[str] = None) -> None:
        """移除工具配置

        Args:
            tool_id: 工具标识
            operator: 操作者标识
        """
        self.tools = [t for t in self.tools if t.tool_id != tool_id]
        self.touch(operator)

    def add_knowledge_source(
        self,
        source_config: KnowledgeSourceConfig,
        operator: Optional[str] = None,
    ) -> None:
        """添加知识源配置

        Args:
            source_config: 知识源配置
            operator: 操作者标识
        """
        existing_ids = [s.source_id for s in self.knowledge_sources]
        if source_config.source_id not in existing_ids:
            self.knowledge_sources.append(source_config)
            self.touch(operator)

    def remove_knowledge_source(self, source_id: str, operator: Optional[str] = None) -> None:
        """移除知识源配置

        Args:
            source_id: 知识源标识
            operator: 操作者标识
        """
        self.knowledge_sources = [
            s for s in self.knowledge_sources if s.source_id != source_id
        ]
        self.touch(operator)
