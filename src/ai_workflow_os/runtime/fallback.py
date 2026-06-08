"""
模型降级策略模块

管理 LLM 模型的降级策略，当首选模型不可用时，
自动按优先级尝试备选模型，确保服务可用性。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 数据类定义 ====================

@dataclass
class ModelConfig:
    """模型配置

    Attributes:
        model_name: 模型名称
        provider: 模型提供商（如 openai、anthropic、local）
        max_tokens: 最大 token 数
        cost_per_token: 每 token 成本（美元）
        priority: 优先级（数值越小优先级越高）
        is_available: 是否可用
        metadata: 附加配置信息
    """
    model_name: str = ""
    provider: str = ""
    max_tokens: int = 4096
    cost_per_token: float = 0.0
    priority: int = 0
    is_available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackResult:
    """降级执行结果

    Attributes:
        success: 是否执行成功
        model_used: 实际使用的模型名称
        output: 模型输出内容
        error: 错误信息（如果失败）
        attempts: 尝试次数
        fallback_occurred: 是否发生了降级
    """
    success: bool = False
    model_used: str = ""
    output: str = ""
    error: str = ""
    attempts: int = 0
    fallback_occurred: bool = False


# ==================== 异常定义 ====================

class AllModelsFailedError(Exception):
    """所有模型均失败异常

    当降级链中的所有模型都不可用或执行失败时抛出。
    """

    def __init__(self, attempted_models: list[str]) -> None:
        """初始化异常

        Args:
            attempted_models: 已尝试的模型名称列表
        """
        self.attempted_models = attempted_models
        super().__init__(
            f"所有模型均失败，已尝试: {', '.join(attempted_models)}"
        )


# ==================== 模型降级管理器 ====================

class ModelFallback:
    """模型降级管理器

    管理 LLM 模型的降级策略，按优先级尝试模型列表，
    当首选模型不可用时自动切换到备选模型。

    Attributes:
        model_chain: 模型配置链（按优先级排序）
        current_model_index: 当前使用的模型索引
        _error_handlers: 错误类型与是否降级的映射
    """

    def __init__(self, model_configs: list[ModelConfig] | None = None) -> None:
        """初始化模型降级管理器

        Args:
            model_configs: 模型配置列表，为空时使用默认配置
        """
        self.model_chain: list[ModelConfig] = model_configs or []
        self.current_model_index: int = 0
        self._error_handlers: dict[type[Exception], bool] = {
            ConnectionError: True,
            TimeoutError: True,
            PermissionError: False,
        }

        # 按优先级排序
        self._sort_model_chain()

        logger.info(
            "模型降级管理器已初始化 (模型数: %d)",
            len(self.model_chain),
        )

    # ==================== 模型链管理 ====================

    def _sort_model_chain(self) -> None:
        """按优先级排序模型链"""
        self.model_chain.sort(key=lambda config: config.priority)

    def add_model(self, config: ModelConfig) -> None:
        """添加模型到降级链

        Args:
            config: 模型配置
        """
        self.model_chain.append(config)
        self._sort_model_chain()
        logger.info(
            "已添加模型: %s (优先级: %d, 提供商: %s)",
            config.model_name,
            config.priority,
            config.provider,
        )

    def remove_model(self, model_name: str) -> bool:
        """从降级链移除模型

        Args:
            model_name: 模型名称

        Returns:
            bool: 移除成功返回 True，模型不存在返回 False
        """
        for i, config in enumerate(self.model_chain):
            if config.model_name == model_name:
                self.model_chain.pop(i)
                # 调整当前索引
                if self.current_model_index >= len(self.model_chain):
                    self.current_model_index = max(0, len(self.model_chain) - 1)
                logger.info("已移除模型: %s", model_name)
                return True

        logger.warning("模型 '%s' 不存在于降级链中", model_name)
        return False

    # ==================== 降级执行 ====================

    async def execute_with_fallback(
        self,
        prompt: str,
        execute_func: Any = None,
        **kwargs: Any,
    ) -> FallbackResult:
        """按优先级尝试模型执行

        Args:
            prompt: 输入 Prompt
            execute_func: 模型执行函数，签名 async (model_config, prompt, **kwargs) -> str
            **kwargs: 传递给执行函数的额外参数

        Returns:
            FallbackResult: 执行结果

        Raises:
            AllModelsFailedError: 当所有模型均失败时抛出
        """
        if not self.model_chain:
            raise AllModelsFailedError([])

        attempted_models: list[str] = []
        last_error: Exception | None = None

        # 从当前索引开始尝试
        for index in range(self.current_model_index, len(self.model_chain)):
            model_config = self.model_chain[index]
            attempted_models.append(model_config.model_name)

            # 检查模型是否可用
            if not model_config.is_available:
                logger.info("模型 '%s' 不可用，跳过", model_config.model_name)
                continue

            try:
                # 尝试执行
                output = await self.try_model(model_config, prompt, execute_func, **kwargs)

                # 执行成功，更新当前索引
                self.current_model_index = index
                fallback_occurred = index > 0

                if fallback_occurred:
                    logger.warning(
                        "已降级到模型 '%s' (原首选: %s)",
                        model_config.model_name,
                        self.model_chain[0].model_name,
                    )

                return FallbackResult(
                    success=True,
                    model_used=model_config.model_name,
                    output=output,
                    attempts=len(attempted_models),
                    fallback_occurred=fallback_occurred,
                )

            except Exception as error:
                last_error = error
                logger.warning(
                    "模型 '%s' 执行失败: %s",
                    model_config.model_name,
                    str(error),
                )

                # 判断是否应该降级
                if not self._should_fallback(error):
                    logger.error(
                        "错误类型不支持降级，停止尝试: %s",
                        type(error).__name__,
                    )
                    break

                # 标记模型不可用
                model_config.is_available = False

        # 所有模型均失败
        error_msg = str(last_error) if last_error else "未知错误"
        return FallbackResult(
            success=False,
            error=error_msg,
            attempts=len(attempted_models),
            fallback_occurred=len(attempted_models) > 1,
        )

    async def try_model(
        self,
        model_config: ModelConfig,
        prompt: str,
        execute_func: Any = None,
        **kwargs: Any,
    ) -> str:
        """尝试特定模型

        Args:
            model_config: 模型配置
            prompt: 输入 Prompt
            execute_func: 模型执行函数
            **kwargs: 额外参数

        Returns:
            str: 模型输出内容

        Raises:
            Exception: 模型执行失败时抛出原始异常
        """
        if execute_func:
            return await execute_func(model_config, prompt, **kwargs)

        # 默认实现：抛出未配置异常
        raise NotImplementedError(
            f"未配置模型执行函数，无法调用模型: {model_config.model_name}"
        )

    def _should_fallback(self, error: Exception) -> bool:
        """判断是否应该降级

        根据错误类型决定是否触发降级。

        Args:
            error: 异常对象

        Returns:
            bool: 应该降级返回 True
        """
        # 检查注册的错误处理器
        for error_type, should_fallback in self._error_handlers.items():
            if isinstance(error, error_type):
                return should_fallback

        # 默认对未知错误进行降级
        return True

    # ==================== 模型查询 ====================

    def get_current_model(self) -> ModelConfig | None:
        """获取当前使用的模型配置

        Returns:
            ModelConfig: 当前模型配置，无可用模型返回 None
        """
        if not self.model_chain:
            return None

        if 0 <= self.current_model_index < len(self.model_chain):
            return self.model_chain[self.current_model_index]

        return None

    def get_available_models(self) -> list[ModelConfig]:
        """获取所有可用模型

        Returns:
            list: 可用模型配置列表
        """
        return [config for config in self.model_chain if config.is_available]

    # ==================== 重置与恢复 ====================

    def reset(self) -> None:
        """重置到首选模型

        将当前索引重置为 0，并恢复所有模型的可用状态。
        """
        self.current_model_index = 0
        for config in self.model_chain:
            config.is_available = True
        logger.info("模型降级管理器已重置到首选模型")

    def restore_model(self, model_name: str) -> bool:
        """恢复指定模型的可用状态

        Args:
            model_name: 模型名称

        Returns:
            bool: 恢复成功返回 True，模型不存在返回 False
        """
        for config in self.model_chain:
            if config.model_name == model_name:
                config.is_available = True
                logger.info("已恢复模型 '%s' 的可用状态", model_name)
                return True

        logger.warning("模型 '%s' 不存在", model_name)
        return False

    # ==================== 统计信息 ====================

    def get_statistics(self) -> dict[str, Any]:
        """获取降级管理器统计信息

        Returns:
            dict: 统计信息
        """
        available_count = sum(1 for c in self.model_chain if c.is_available)
        current_model = self.get_current_model()

        return {
            "total_models": len(self.model_chain),
            "available_models": available_count,
            "current_model": current_model.model_name if current_model else None,
            "current_provider": current_model.provider if current_model else None,
            "model_chain": [
                {
                    "model_name": c.model_name,
                    "provider": c.provider,
                    "priority": c.priority,
                    "is_available": c.is_available,
                }
                for c in self.model_chain
            ],
        }
