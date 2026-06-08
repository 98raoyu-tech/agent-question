"""
应用启动入口

解析命令行参数，配置日志，启动uvicorn服务器。
"""

import argparse
import logging
import sys
from pathlib import Path

import structlog
import uvicorn


def setup_logging(log_level: str = "INFO") -> None:
    """配置structlog日志

    Args:
        log_level: 日志级别
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def parse_args() -> argparse.Namespace:
    """解析命令行参数

    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description="Enterprise AI Workflow OS - 应用服务器",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器监听地址 (默认: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器监听端口 (默认: 8000)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量 (默认: 1)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别 (默认: INFO)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="开启热重载模式 (开发环境使用)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="开启调试模式",
    )

    return parser.parse_args()


def main() -> None:
    """应用主入口函数"""
    args = parse_args()

    # 配置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info(
        f"正在启动 Enterprise AI Workflow OS...",
        extra={
            "host": args.host,
            "port": args.port,
            "workers": args.workers,
            "log_level": args.log_level,
            "reload": args.reload,
            "debug": args.debug,
        },
    )

    # 启动uvicorn服务器
    uvicorn.run(
        "ai_workflow_os.api.app:app",
        host=args.host,
        port=args.port,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level.lower(),
        reload=args.reload,
        access_log=True,
    )


if __name__ == "__main__":
    main()
