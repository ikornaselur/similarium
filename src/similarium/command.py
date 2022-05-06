import datetime as dt
from typing import Optional

from dateutil import parser

from similarium.exceptions import ParseException


class Command:
    @property
    def text(self) -> str:
        raise NotImplementedError()

    @property
    def blocks(self) -> Optional[list[dict]]:
        return None

    def __repr__(self) -> str:
        return "<Command>"


class Start(Command):
    when: dt.time
    timezone: str

    def __init__(self, when: dt.time) -> None:
        self.when = when

    @property
    def when_human(self) -> str:
        when_fmt = self.when.strftime("%H:%M")

        if 0 <= self.when.hour < 4:
            return f"late night at {when_fmt}"
        elif 4 <= self.when.hour < 8:
            return f"in the early morning at {when_fmt}"
        elif 8 <= self.when.hour < 12:
            return f"in the morning at {when_fmt}"
        elif 12 <= self.when.hour < 13:
            return f"at noon at {when_fmt}"
        elif 13 <= self.when.hour < 17:
            return f"in the afternoon at {when_fmt}"
        elif 17 <= self.when.hour < 21:
            return f"in the evening at {when_fmt}"
        elif 21 <= self.when.hour < 24:
            return f"at night at {when_fmt}"
        else:
            return f"at {when_fmt}"

    @property
    def text(self) -> str:
        return f":white_check_mark: Will post the daily puzzle {self.when_human}!"

    def __repr__(self) -> str:
        return f"<Start ({self.when_human}))>"


class Stop(Command):
    @property
    def text(self) -> str:
        return ":white_check_mark: Will stop posting the daily puzzle!"

    def __repr__(self) -> str:
        return "<Stop>"


class Help(Command):
    @property
    def text(self) -> str:
        return "Hello there :wave: here's what you can do!"

    @property
    def blocks(self) -> list[dict]:
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello there :wave: here's what you can do!",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Start a daily puzzle at a specific time*\nStart posting a"
                        " daily puzzle at the provided time on the current channel. The"
                        ' time can be something like "9am" or "13:00" for example.\nThe'
                        " time will be based on your timezone."
                    ),
                },
                "fields": [
                    {"type": "mrkdwn", "text": "Start a daily puzzle"},
                    {"type": "mrkdwn", "text": "`/similarium start [time]`"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Stop posting the daily puzzle*\nStop posting a daily puzzle"
                        " if there is one"
                    ),
                },
                "fields": [
                    {"type": "mrkdwn", "text": "Stop a daily puzzle"},
                    {"type": "mrkdwn", "text": "`/similarium stop`"},
                ],
            },
        ]

    def __repr__(self) -> str:
        return "<Help>"


def parse_command(text: str) -> Command:
    parts = text.split(" ")
    subcommand = parts[0]

    if subcommand == "start":
        if len(parts) < 2:
            raise ParseException(
                ":no_entry_sign: Time missing from start command :no_entry_sign:"
            )
        # Try to parse the time
        try:
            time = parser.parse(parts[1]).time()
        except parser.ParserError:
            raise ParseException(
                "Unable to parse time. Try tomething like 9am or 13:00"
            )
        return Start(when=time)
    elif subcommand == "stop":
        return Stop()
    elif subcommand == "help":
        return Help()
    else:
        raise ParseException(":no_entry_sign: Unknown command :no_entry_sign:")
