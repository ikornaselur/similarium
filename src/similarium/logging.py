import logging

from rich.logging import RichHandler

from similarium.config import config

logger = logging.getLogger("similarium")
web_logger = logging.getLogger("similarium.web")
logger.setLevel(config.logging.log_level)
web_logger.setLevel(config.logging.web_log_level)


def configure_logger() -> None:

    logger.handlers.clear()
    logger.addHandler(RichHandler(log_time_format="[%X]", markup=False))

    web_logger.handlers.clear()
    web_logger.addHandler(RichHandler(log_time_format="[%X]", markup=False))
