import logging
import sys
from typing import Literal

from loguru import logger

from app.core.config import settings


LOGGING_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
    "| <level>{level: <8}</level> "
    "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "- <level>{message}</level>"
)


def configure_logging(level: str | Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = None) -> None:
    """
    使用 Loguru 配置统一日志格式，兼容标准 logging。
    """

    logger.remove()
    log_level = (level or settings.log_level).upper()
    logger.add(sys.stdout, level=log_level, format=LOGGING_FORMAT, colorize=True)

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelname, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=log_level)

