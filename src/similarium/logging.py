import logging
import os

from rich.logging import RichHandler

logging.basicConfig(
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(log_time_format="[%X]", markup=False)],
)

logger = logging.getLogger("similarium")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
