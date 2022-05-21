from asyncio.events import AbstractEventLoop
from typing import Any

import sentry_sdk

from similarium.logging import logger


def exception_handler(loop: AbstractEventLoop, context: dict[str, Any]) -> None:
    exception = context.get("exception")
    logger.error("Global exception handler got exception", exc_info=exception)

    if exception:
        sentry_sdk.capture_exception(exception)
    else:
        sentry_sdk.capture_message("Got unexpected asyncio exception")


def init_exception_handler(loop: AbstractEventLoop):
    loop.set_exception_handler(exception_handler)


class SimilariumException(Exception):
    pass


class InvalidWord(SimilariumException):
    pass


class ParseException(SimilariumException):
    pass


class SlackException(SimilariumException):
    pass


class ChannelNotFound(SlackException):
    pass


class NotInChannel(SlackException):
    pass


class AccountInactive(SlackException):
    pass


class GameNotRegistered(SlackException):
    pass


class DatabaseException(SimilariumException):
    pass


class NotFound(DatabaseException):
    pass
