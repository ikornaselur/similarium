import logging
import os

from rich.logging import RichHandler

logger = logging.getLogger("similarium")
web_logger = logging.getLogger("similarium.web")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
web_logger.setLevel(os.environ.get("LOG_LEVEL", "WARNING"))


def configure_logger() -> None:
    logger.handlers.clear()
    logger.addHandler(RichHandler(log_time_format="[%X]", markup=False))

    web_logger.handlers.clear()
    web_logger.addHandler(RichHandler(log_time_format="[%X]", markup=False))
