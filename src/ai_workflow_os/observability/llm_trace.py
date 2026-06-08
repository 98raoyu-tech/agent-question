"""
Langfuse LLM追踪模块

集成Langfuse的LLM调用追踪，支持追踪LLM生成、Span记录和元数据管理。
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LLMTracer:
    """Langfuse LLM追踪器"""

    def __init__(self) -> None:
        """初始化LLM追踪器"""
        self._langfuse_client: Optional[Any] = None
        self._initialized: bool = False
        self._active_traces: dict[str, dict] = {}

    def initialize(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
    ) -> None:
        """初始化Langfuse客户端

        Args:
            public_key: Langfuse公钥，默认从环境变量LANGFUSE_PUBLIC_KEY读取
            secret_key: Langfuse私钥，默认从环境变量LANGFUSE_SECRET_KEY读取
            host: Langfuse服务地址，默认从环境变量LANGFUSE_HOST读取
        """
        if self._initialized:
            logger.warning("LLM追踪器已初始化，跳过重复初始化")
            return

        # 从环境变量读取配置
        public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        # 检查必需的配置
        if not public_key or not secret_key:
            logger.warning(
                "Langfuse配置不完整，LLM追踪功能将使用本地模式。"
                "请设置LANGFUSE_PUBLIC_KEY和LANGFUSE_SECRET_KEY环境变量。"
            )
            self._initialized = True
            return

        try:
            from langfuse import Langfuse

            self._langfuse_client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            self._initialized = True
            logger.info(f"Langfuse客户端初始化完成，服务地址: {host}")
        except ImportError:
            logger.warning("langfuse包未安装，LLM追踪功能将使用本地模式")
            self._initialized = True
        except Exception as e:
            logger.error(f"Langfuse客户端初始化失败: {str(e)}")
            self._initialized = True

    def start_trace(
        self,
        name: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """开始追踪

        Args:
            name: 追踪名称
            metadata: 追踪元数据

        Returns:
            追踪ID
        """
        trace_id = str(uuid.uuid4())

        # 本地记录追踪信息
        self._active_traces[trace_id] = {
            "name": name,
            "metadata": metadata or {},
            "started_at": datetime.now(timezone.utc).isoformat(),
            "generations": [],
            "spans": [],
        }

        # 如果Langfuse客户端可用，同步创建追踪
        if self._langfuse_client:
            try:
                self._langfuse_client.trace(
                    id=trace_id,
                    name=name,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Langfuse创建追踪失败: {str(e)}")

        logger.debug(f"开始追踪: {name} (ID: {trace_id})")
        return trace_id

    def log_generation(
        self,
        trace_id: str,
        model: str,
        prompt: Any,
        response: Any,
        usage: Optional[dict[str, int]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """记录LLM生成

        Args:
            trace_id: 追踪ID
            model: 模型名称
            prompt: 输入提示
            response: 模型响应
            usage: Token使用量 (prompt_tokens, completion_tokens, total_tokens)
            metadata: 额外元数据

        Returns:
            生成记录ID
        """
        generation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # 本地记录
        generation_record = {
            "id": generation_id,
            "model": model,
            "prompt": str(prompt)[:1000],  # 截断长内容
            "response": str(response)[:1000],
            "usage": usage or {},
            "metadata": metadata or {},
            "timestamp": now,
        }

        if trace_id in self._active_traces:
            self._active_traces[trace_id]["generations"].append(generation_record)

        # 如果Langfuse客户端可用，同步记录
        if self._langfuse_client:
            try:
                self._langfuse_client.generation(
                    id=generation_id,
                    trace_id=trace_id,
                    model=model,
                    input=prompt,
                    output=response,
                    usage=usage,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Langfuse记录生成失败: {str(e)}")

        logger.debug(
            f"记录LLM生成: 模型={model}, 追踪ID={trace_id}, 生成ID={generation_id}"
        )
        return generation_id

    def log_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """记录Span

        Args:
            trace_id: 追踪ID
            name: Span名称
            input_data: 输入数据
            output_data: 输出数据
            metadata: 额外元数据

        Returns:
            Span ID
        """
        span_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # 本地记录
        span_record = {
            "id": span_id,
            "name": name,
            "input": str(input_data)[:1000],
            "output": str(output_data)[:1000],
            "metadata": metadata or {},
            "timestamp": now,
        }

        if trace_id in self._active_traces:
            self._active_traces[trace_id]["spans"].append(span_record)

        # 如果Langfuse客户端可用，同步记录
        if self._langfuse_client:
            try:
                self._langfuse_client.span(
                    id=span_id,
                    trace_id=trace_id,
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error(f"Langfuse记录Span失败: {str(e)}")

        logger.debug(f"记录Span: {name}, 追踪ID={trace_id}, SpanID={span_id}")
        return span_id

    def end_trace(
        self,
        trace_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """结束追踪

        Args:
            trace_id: 追踪ID
            metadata: 额外元数据
        """
        if trace_id in self._active_traces:
            self._active_traces[trace_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            if metadata:
                self._active_traces[trace_id]["metadata"].update(metadata)

        # 如果Langfuse客户端可用，刷新数据
        if self._langfuse_client:
            try:
                self._langfuse_client.flush()
            except Exception as e:
                logger.error(f"Langfuse刷新数据失败: {str(e)}")

        logger.debug(f"结束追踪: {trace_id}")

    def get_trace(self, trace_id: str) -> Optional[dict]:
        """获取追踪信息

        Args:
            trace_id: 追踪ID

        Returns:
            追踪信息字典，不存在则返回None
        """
        return self._active_traces.get(trace_id)

    @staticmethod
    def create_generation_metadata(
        model: str,
        tokens: Optional[dict[str, int]] = None,
        latency: Optional[float] = None,
    ) -> dict[str, Any]:
        """创建生成元数据

        Args:
            model: 模型名称
            tokens: Token使用量
            latency: 延迟时间（秒）

        Returns:
            元数据字典
        """
        metadata = {
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if tokens:
            metadata["tokens"] = tokens

        if latency is not None:
            metadata["latency_seconds"] = round(latency, 3)

        return metadata

    def shutdown(self) -> None:
        """关闭LLM追踪器，清理资源"""
        if self._langfuse_client:
            try:
                self._langfuse_client.flush()
            except Exception as e:
                logger.error(f"Langfuse关闭时刷新数据失败: {str(e)}")

        self._active_traces.clear()
        self._initialized = False
        logger.info("LLM追踪器已关闭")


# 全局LLM追踪器实例
llm_tracer = LLMTracer()
