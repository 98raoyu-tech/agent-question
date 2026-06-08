"""
Agent适配器抽象基类

定义所有Agent框架适配器的统一接口，支持多种Agent框架（LangChain、LangGraph、CrewAI、AutoGen、MCP）。
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any

from .enums import AdapterStatus, AdapterType


class AgentAdapter(ABC):
    """Agent适配器抽象基类

    所有具体框架适配器必须继承此类并实现抽象方法。
    提供统一的Agent调用接口，屏蔽底层框架差异。

    Attributes:
        id: 适配器唯一标识
        status: 适配器当前状态
        config: 适配器配置
        created_by: 创建者标识
        updated_by: 更新者标识
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """初始化适配器

        Args:
            config: 适配器配置
        """
        self.id: str = uuid.uuid4().hex
        self.status: AdapterStatus = AdapterStatus.INACTIVE
        self.config: dict[str, Any] = config
        self.created_by: str | None = None
        self.updated_by: str | None = None

    @property
    @abstractmethod
    def adapter_type(self) -> AdapterType:
        """获取适配器类型

        Returns:
            适配器类型枚举值
        """
        ...

    @abstractmethod
    async def invoke(self, input_data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """调用Agent执行任务

        Args:
            input_data: 输入数据
            config: 调用级配置（覆盖适配器默认配置）

        Returns:
            Agent执行结果

        Raises:
            RuntimeError: 调用失败时抛出
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """执行健康检查

        Returns:
            适配器是否健康
        """
        ...

    @abstractmethod
    async def metrics(self) -> dict[str, Any]:
        """获取适配器运行指标

        Returns:
            指标数据字典
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """关闭适配器，释放资源"""
        ...

    def is_healthy(self) -> bool:
        """判断适配器是否处于健康状态

        基于适配器状态进行快速判断，不执行实际的健康检查。

        Returns:
            是否健康
        """
        return self.status == AdapterStatus.ACTIVE
