import logging
import os

from rich.logging import RichHandler

logger = logging.getLogger("similarium")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def configure_logger() -> None:
    logger.handlers.clear()
    logger.addHandler(RichHandler(log_time_format="[%X]", markup=False))
