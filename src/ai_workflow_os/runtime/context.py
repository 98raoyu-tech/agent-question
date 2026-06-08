"""
Context 管理模块（Prompt 生命周期）

管理 Prompt 和上下文的完整生命周期，支持：
- 上下文创建与销毁
- 消息追加与截断
- 上下文压缩（使用 LLM 摘要）
- Token 计数管理
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# 配置日志记录器
logger = logging.getLogger(__name__)


# ==================== 常量定义 ====================

# 默认最大上下文大小（token 数）
DEFAULT_MAX_CONTEXT_SIZE: int = 128000

# 默认消息截断保留比例
TRUNCATE_KEEP_RATIO: float = 0.6


# ==================== 数据类定义 ====================

@dataclass
class ContextMessage:
    """上下文消息

    Attributes:
        role: 消息角色（system/user/assistant/tool）
        content: 消息内容
        token_count: 消息 token 数量
        timestamp: 消息时间戳
        metadata: 附加元数据
    """
    role: str = ""
    content: str = ""
    token_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """上下文窗口

    Attributes:
        context_id: 上下文唯一标识
        agent_id: 所属 Agent ID
        messages: 消息列表
        total_tokens: 总 token 数量
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    context_id: str = ""
    agent_id: str = ""
    messages: list[ContextMessage] = field(default_factory=list)
    total_tokens: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== 上下文管理器 ====================

class ContextManager:
    """上下文管理器

    管理 Prompt 和上下文的完整生命周期，提供上下文的创建、
    追加、截断、压缩和销毁等操作。

    Attributes:
        contexts: 上下文窗口映射，键为 context_id
        max_context_size: 最大上下文大小（token 数）
    """

    def __init__(self, max_context_size: int = DEFAULT_MAX_CONTEXT_SIZE) -> None:
        """初始化上下文管理器

        Args:
            max_context_size: 最大上下文大小（token 数）
        """
        self.contexts: dict[str, ContextWindow] = {}
        self.max_context_size: int = max_context_size
        logger.info(
            "上下文管理器已初始化 (最大上下文: %d tokens)", max_context_size
        )

    # ==================== 上下文创建与销毁 ====================

    def create_context(
        self, agent_id: str, initial_prompt: str
    ) -> str:
        """创建上下文

        为指定 Agent 创建新的上下文窗口，并写入初始 Prompt。

        Args:
            agent_id: Agent ID
            initial_prompt: 初始 Prompt 内容

        Returns:
            str: 上下文 ID
        """
        context_id = uuid.uuid4().hex[:12]

        # 创建初始系统消息
        initial_message = ContextMessage(
            role="system",
            content=initial_prompt,
            token_count=self._estimate_token_count(initial_prompt),
        )

        # 创建上下文窗口
        context_window = ContextWindow(
            context_id=context_id,
            agent_id=agent_id,
            messages=[initial_message],
            total_tokens=initial_message.token_count,
        )

        self.contexts[context_id] = context_window

        logger.info(
            "已为 Agent '%s' 创建上下文: %s (初始 tokens: %d)",
            agent_id,
            context_id,
            initial_message.token_count,
        )
        return context_id

    def destroy_context(self, context_id: str) -> None:
        """销毁上下文

        释放指定上下文的所有资源。

        Args:
            context_id: 上下文 ID
        """
        if context_id not in self.contexts:
            logger.warning("上下文 '%s' 不存在，无法销毁", context_id)
            return

        del self.contexts[context_id]
        logger.info("已销毁上下文: %s", context_id)

    # ==================== 消息操作 ====================

    def append_to_context(
        self, context_id: str, message: dict[str, Any]
    ) -> None:
        """追加消息到上下文

        Args:
            context_id: 上下文 ID
            message: 消息数据，需包含 role 和 content 字段

        Raises:
            ValueError: 当上下文不存在或消息格式错误时抛出
        """
        context = self._get_context_or_raise(context_id)

        # 验证消息格式
        role = message.get("role", "")
        content = message.get("content", "")
        if not role or not content:
            raise ValueError("消息必须包含 role 和 content 字段")

        # 创建消息对象
        token_count = self._estimate_token_count(content)
        context_message = ContextMessage(
            role=role,
            content=content,
            token_count=token_count,
            metadata=message.get("metadata", {}),
        )

        # 追加消息
        context.messages.append(context_message)
        context.total_tokens += token_count
        context.updated_at = datetime.now(timezone.utc)

        logger.debug(
            "已追加消息到上下文 '%s' (角色: %s, tokens: %d, 总 tokens: %d)",
            context_id,
            role,
            token_count,
            context.total_tokens,
        )

    def truncate_context(
        self, context_id: str, max_tokens: int | None = None
    ) -> int:
        """截断上下文

        保留最近的消息，移除较早的消息以满足 token 限制。

        Args:
            context_id: 上下文 ID
            max_tokens: 最大 token 数，为 None 时使用默认值

        Returns:
            int: 被移除的消息数量

        Raises:
            ValueError: 当上下文不存在时抛出
        """
        context = self._get_context_or_raise(context_id)
        target_tokens = max_tokens or self.max_context_size

        # 如果当前 token 数未超限，无需截断
        if context.total_tokens <= target_tokens:
            return 0

        # 计算需要保留的消息数
        keep_count = max(1, int(len(context.messages) * TRUNCATE_KEEP_RATIO))

        # 始终保留第一条系统消息
        system_messages = [
            msg for msg in context.messages if msg.role == "system"
        ]
        other_messages = [
            msg for msg in context.messages if msg.role != "system"
        ]

        # 从最新的消息开始保留
        kept_other = other_messages[-keep_count:] if keep_count <= len(other_messages) else other_messages

        # 计算保留后的 token 数
        kept_messages = system_messages + kept_other
        kept_tokens = sum(msg.token_count for msg in kept_messages)

        # 如果仍然超限，继续减少
        while kept_tokens > target_tokens and len(kept_other) > 1:
            removed = kept_other.pop(0)
            kept_tokens -= removed.token_count

        removed_count = len(context.messages) - len(kept_messages)

        # 更新上下文
        context.messages = kept_messages
        context.total_tokens = kept_tokens
        context.updated_at = datetime.now(timezone.utc)

        logger.info(
            "已截断上下文 '%s': 移除 %d 条消息，剩余 tokens: %d",
            context_id,
            removed_count,
            kept_tokens,
        )
        return removed_count

    # ==================== 上下文查询 ====================

    def get_context(self, context_id: str) -> ContextWindow | None:
        """获取上下文

        Args:
            context_id: 上下文 ID

        Returns:
            ContextWindow: 上下文窗口，不存在返回 None
        """
        return self.contexts.get(context_id)

    def get_context_messages(
        self, context_id: str
    ) -> list[dict[str, Any]]:
        """获取上下文消息列表（字典格式）

        Args:
            context_id: 上下文 ID

        Returns:
            list: 消息字典列表
        """
        context = self.contexts.get(context_id)
        if not context:
            return []

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "token_count": msg.token_count,
            }
            for msg in context.messages
        ]

    # ==================== 上下文压缩 ====================

    async def compress_context(self, context_id: str) -> str:
        """压缩历史上下文

        使用 LLM 对历史消息进行摘要压缩，减少 token 占用。
        保留最近的消息，将较早的消息压缩为摘要。

        Args:
            context_id: 上下文 ID

        Returns:
            str: 压缩后的摘要内容

        Raises:
            ValueError: 当上下文不存在时抛出
        """
        context = self._get_context_or_raise(context_id)

        # 如果消息数量较少，无需压缩
        if len(context.messages) <= 3:
            return ""

        # 分离系统消息、历史消息和最近消息
        system_messages = [
            msg for msg in context.messages if msg.role == "system"
        ]
        non_system_messages = [
            msg for msg in context.messages if msg.role != "system"
        ]

        # 保留最近 4 条消息
        recent_count = 4
        recent_messages = non_system_messages[-recent_count:]
        historical_messages = non_system_messages[:-recent_count]

        if not historical_messages:
            return ""

        # 构建摘要请求
        history_text = "\n".join(
            f"[{msg.role}]: {msg.content}" for msg in historical_messages
        )
        summary_prompt = (
            f"请将以下对话历史压缩为简洁的摘要，保留关键信息：\n\n{history_text}"
        )

        # TODO: 集成实际的 LLM 调用进行摘要
        # 目前使用简单的截断作为占位实现
        summary = f"[历史摘要] 共 {len(historical_messages)} 条消息已压缩"

        # 重建上下文
        summary_message = ContextMessage(
            role="system",
            content=summary,
            token_count=self._estimate_token_count(summary),
        )

        context.messages = system_messages + [summary_message] + recent_messages
        context.total_tokens = sum(msg.token_count for msg in context.messages)
        context.updated_at = datetime.now(timezone.utc)

        logger.info(
            "已压缩上下文 '%s': 历史 %d 条消息 -> 摘要，总 tokens: %d",
            context_id,
            len(historical_messages),
            context.total_tokens,
        )
        return summary

    # ==================== 内部工具方法 ====================

    def _get_context_or_raise(self, context_id: str) -> ContextWindow:
        """获取上下文或抛出异常

        Args:
            context_id: 上下文 ID

        Returns:
            ContextWindow: 上下文窗口

        Raises:
            ValueError: 当上下文不存在时抛出
        """
        context = self.contexts.get(context_id)
        if not context:
            raise ValueError(f"上下文 '{context_id}' 不存在")
        return context

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        """估算文本的 token 数量

        使用简化的估算规则：
        - 英文约 4 个字符 = 1 token
        - 中文约 1.5 个字符 = 1 token

        Args:
            text: 待估算的文本

        Returns:
            int: 估算的 token 数量
        """
        if not text:
            return 0

        # 统计中文字符数
        chinese_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        # 统计非中文字符数
        non_chinese_count = len(text) - chinese_count

        # 分别估算
        chinese_tokens = int(chinese_count / 1.5)
        english_tokens = int(non_chinese_count / 4)

        return max(1, chinese_tokens + english_tokens)

    # ==================== 统计信息 ====================

    def get_statistics(self) -> dict[str, Any]:
        """获取上下文管理器统计信息

        Returns:
            dict: 统计信息
        """
        total_contexts = len(self.contexts)
        total_tokens = sum(ctx.total_tokens for ctx in self.contexts.values())
        total_messages = sum(len(ctx.messages) for ctx in self.contexts.values())

        return {
            "total_contexts": total_contexts,
            "total_tokens": total_tokens,
            "total_messages": total_messages,
            "max_context_size": self.max_context_size,
        }
