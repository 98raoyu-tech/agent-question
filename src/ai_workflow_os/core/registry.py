"""
组件注册中心模块

采用单例模式管理所有可插拔组件（Agent、Tool、Workflow）的注册与获取。
使用 threading.Lock 保证多线程环境下的安全性。
"""

import threading
from typing import Any, Dict, Optional, Type


class Registry:
    """
    组件注册中心（单例模式）

    负责管理平台中所有可插拔组件的注册表，包括：
    - Agent 类型
    - Tool 处理器
    - Workflow 类型

    使用示例：
        registry = Registry()
        registry.register_agent("chat_agent", ChatAgent)
        agent_cls = registry.get_agent("chat_agent")
    """

    _instance: Optional["Registry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "Registry":
        """确保单例模式，使用双重检查锁"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化注册表存储结构"""
        if self._initialized:
            return

        self._agents: Dict[str, Type] = {}
        self._tools: Dict[str, Any] = {}
        self._workflows: Dict[str, Type] = {}
        self._data_lock: threading.Lock = threading.Lock()
        self._initialized = True

    # =========================================================================
    # Agent 注册与获取
    # =========================================================================

    def register_agent(self, agent_type: str, agent_class: Type) -> None:
        """
        注册 Agent 类型

        Args:
            agent_type: Agent 类型标识符
            agent_class: Agent 类

        Raises:
            ValueError: 当 agent_type 已存在时抛出
        """
        with self._data_lock:
            if agent_type in self._agents:
                raise ValueError(f"Agent 类型 '{agent_type}' 已注册，如需覆盖请先注销")
            self._agents[agent_type] = agent_class

    def get_agent(self, agent_type: str) -> Optional[Type]:
        """
        获取已注册的 Agent 类

        Args:
            agent_type: Agent 类型标识符

        Returns:
            对应的 Agent 类，未找到时返回 None
        """
        with self._data_lock:
            return self._agents.get(agent_type)

    def unregister_agent(self, agent_type: str) -> bool:
        """
        注销 Agent 类型

        Args:
            agent_type: Agent 类型标识符

        Returns:
            是否成功注销
        """
        with self._data_lock:
            if agent_type in self._agents:
                del self._agents[agent_type]
                return True
            return False

    # =========================================================================
    # Tool 注册与获取
    # =========================================================================

    def register_tool(self, tool_name: str, tool_handler: Any) -> None:
        """
        注册 Tool 处理器

        Args:
            tool_name: 工具名称标识符
            tool_handler: 工具处理器实例或类

        Raises:
            ValueError: 当 tool_name 已存在时抛出
        """
        with self._data_lock:
            if tool_name in self._tools:
                raise ValueError(f"工具 '{tool_name}' 已注册，如需覆盖请先注销")
            self._tools[tool_name] = tool_handler

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        获取已注册的 Tool 处理器

        Args:
            tool_name: 工具名称标识符

        Returns:
            对应的工具处理器，未找到时返回 None
        """
        with self._data_lock:
            return self._tools.get(tool_name)

    def unregister_tool(self, tool_name: str) -> bool:
        """
        注销 Tool 处理器

        Args:
            tool_name: 工具名称标识符

        Returns:
            是否成功注销
        """
        with self._data_lock:
            if tool_name in self._tools:
                del self._tools[tool_name]
                return True
            return False

    # =========================================================================
    # Workflow 注册与获取
    # =========================================================================

    def register_workflow(self, workflow_type: str, workflow_class: Type) -> None:
        """
        注册 Workflow 类型

        Args:
            workflow_type: 工作流类型标识符
            workflow_class: 工作流类

        Raises:
            ValueError: 当 workflow_type 已存在时抛出
        """
        with self._data_lock:
            if workflow_type in self._workflows:
                raise ValueError(f"工作流类型 '{workflow_type}' 已注册，如需覆盖请先注销")
            self._workflows[workflow_type] = workflow_class

    def get_workflow(self, workflow_type: str) -> Optional[Type]:
        """
        获取已注册的 Workflow 类

        Args:
            workflow_type: 工作流类型标识符

        Returns:
            对应的工作流类，未找到时返回 None
        """
        with self._data_lock:
            return self._workflows.get(workflow_type)

    def unregister_workflow(self, workflow_type: str) -> bool:
        """
        注销 Workflow 类型

        Args:
            workflow_type: 工作流类型标识符

        Returns:
            是否成功注销
        """
        with self._data_lock:
            if workflow_type in self._workflows:
                del self._workflows[workflow_type]
                return True
            return False

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def list_agents(self) -> list[str]:
        """列出所有已注册的 Agent 类型"""
        with self._data_lock:
            return list(self._agents.keys())

    def list_tools(self) -> list[str]:
        """列出所有已注册的 Tool 名称"""
        with self._data_lock:
            return list(self._tools.keys())

    def list_workflows(self) -> list[str]:
        """列出所有已注册的 Workflow 类型"""
        with self._data_lock:
            return list(self._workflows.keys())

    def clear(self) -> None:
        """清空所有注册表（主要用于测试）"""
        with self._data_lock:
            self._agents.clear()
            self._tools.clear()
            self._workflows.clear()


# 全局注册中心单例
registry = Registry()