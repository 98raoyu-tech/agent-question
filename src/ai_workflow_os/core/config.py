"""
配置管理模块

使用 pydantic-settings 的 Settings 类集中管理所有配置项，
支持从环境变量和 .env 文件加载配置。
"""

from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/workflow_os",
        description="数据库连接地址",
    )

    model_config = {"env_prefix": "DB_"}


class RedisConfig(BaseSettings):
    """Redis 配置"""

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接地址",
    )

    model_config = {"env_prefix": "REDIS_"}


class Neo4jConfig(BaseSettings):
    """Neo4j 图数据库配置"""

    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j 连接地址",
    )
    NEO4J_USER: str = Field(
        default="neo4j",
        description="Neo4j 用户名",
    )
    NEO4J_PASSWORD: str = Field(
        default="neo4j",
        description="Neo4j 密码",
    )

    model_config = {"env_prefix": "NEO4J_"}


class KafkaConfig(BaseSettings):
    """Kafka 消息队列配置"""

    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka 引导服务器地址",
    )
    KAFKA_TOPICS: Dict[str, str] = Field(
        default={
            "agent_events": "agent-events",
            "workflow_events": "workflow-events",
            "tool_events": "tool-events",
        },
        description="Kafka 主题映射表",
    )

    model_config = {"env_prefix": "KAFKA_"}


class TemporalConfig(BaseSettings):
    """Temporal 工作流引擎配置"""

    TEMPORAL_ADDRESS: str = Field(
        default="localhost:7233",
        description="Temporal 服务地址",
    )
    TEMPORAL_NAMESPACE: str = Field(
        default="default",
        description="Temporal 命名空间",
    )
    TEMPORAL_TASK_QUEUE: str = Field(
        default="workflow-os-task-queue",
        description="Temporal 任务队列名称",
    )

    model_config = {"env_prefix": "TEMPORAL_"}


class AuthConfig(BaseSettings):
    """认证与授权配置"""

    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 签名密钥",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT 签名算法",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="访问令牌过期时间（分钟）",
    )

    model_config = {"env_prefix": "AUTH_"}


class ObservabilityConfig(BaseSettings):
    """可观测性配置（Langfuse、OpenTelemetry）"""

    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(
        default=None,
        description="Langfuse 公钥",
    )
    LANGFUSE_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Langfuse 私钥",
    )
    OTEL_EXPORTER_ENDPOINT: Optional[str] = Field(
        default=None,
        description="OpenTelemetry 导出端点",
    )

    model_config = {"env_prefix": "OBS_"}


class AppConfig(BaseSettings):
    """应用全局配置"""

    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别",
    )
    DEBUG: bool = Field(
        default=False,
        description="调试模式开关",
    )
    WORKERS: int = Field(
        default=4,
        description="工作进程数",
    )

    model_config = {"env_prefix": "APP_"}


class Settings(BaseSettings):
    """
    顶层配置聚合类

    聚合所有子配置模块，提供统一的配置访问入口。
    支持从环境变量和 .env 文件加载配置。
    """

    # 数据库配置
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Redis 配置
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Neo4j 图数据库配置
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)

    # Kafka 消息队列配置
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)

    # Temporal 工作流引擎配置
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)

    # 认证与授权配置
    auth: AuthConfig = Field(default_factory=AuthConfig)

    # 可观测性配置
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

    # 应用全局配置
    app: AppConfig = Field(default_factory=AppConfig)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# 全局配置单例
settings = Settings()