import datetime as dt

import pytest

from similarium.command import Help, Start, Stop, parse_command
from similarium.exceptions import ParseException


def test_parse_command_unknown() -> None:
    with pytest.raises(
        ParseException, match=":no_entry_sign: Unknown command :no_entry_sign:"
    ):
        parse_command("foo bar")


def test_parse_command_no_command() -> None:
    with pytest.raises(
        ParseException, match=":no_entry_sign: Unknown command :no_entry_sign:"
    ):
        parse_command("")


def test_parse_command_help_returns_help() -> None:
    assert isinstance(parse_command("help"), Help)
    assert isinstance(parse_command("help me"), Help)


def test_parse_command_help_has_blocks() -> None:
    help_command = parse_command("help")

    assert isinstance(help_command, Help)
    assert len(help_command.blocks) > 0


def test_parse_command_stop_has_text() -> None:
    stop_command = parse_command("stop")

    assert isinstance(stop_command, Stop)
    assert "Will stop posting the daily puzzle" in stop_command.text


def test_parse_command_start_raises_if_missing_time() -> None:
    with pytest.raises(
        ParseException,
        match=":no_entry_sign: Time missing from start command :no_entry_sign:",
    ):
        parse_command("start")


def test_parse_command_start_sets_when() -> None:
    start_command = parse_command("start 9am")

    assert isinstance(start_command, Start)
    assert start_command.when == dt.time(9, 0)
    assert start_command.when_human == "in the morning at 09:00"


def test_parse_command_start_when_human() -> None:
    assert Start(dt.time(0, 0)).when_human == "late night at 00:00"
    assert Start(dt.time(1, 0)).when_human == "late night at 01:00"
    assert Start(dt.time(2, 0)).when_human == "late night at 02:00"
    assert Start(dt.time(3, 0)).when_human == "late night at 03:00"
    assert Start(dt.time(4, 0)).when_human == "in the early morning at 04:00"
    assert Start(dt.time(5, 0)).when_human == "in the early morning at 05:00"
    assert Start(dt.time(6, 0)).when_human == "in the early morning at 06:00"
    assert Start(dt.time(7, 0)).when_human == "in the early morning at 07:00"
    assert Start(dt.time(8, 0)).when_human == "in the morning at 08:00"
    assert Start(dt.time(9, 0)).when_human == "in the morning at 09:00"
    assert Start(dt.time(10, 0)).when_human == "in the morning at 10:00"
    assert Start(dt.time(11, 0)).when_human == "in the morning at 11:00"
    assert Start(dt.time(12, 0)).when_human == "at noon at 12:00"
    assert Start(dt.time(13, 0)).when_human == "in the afternoon at 13:00"
    assert Start(dt.time(14, 0)).when_human == "in the afternoon at 14:00"
    assert Start(dt.time(15, 0)).when_human == "in the afternoon at 15:00"
    assert Start(dt.time(16, 0)).when_human == "in the afternoon at 16:00"
    assert Start(dt.time(17, 0)).when_human == "in the evening at 17:00"
    assert Start(dt.time(18, 0)).when_human == "in the evening at 18:00"
    assert Start(dt.time(19, 0)).when_human == "in the evening at 19:00"
    assert Start(dt.time(20, 0)).when_human == "in the evening at 20:00"
    assert Start(dt.time(21, 0)).when_human == "at night at 21:00"
    assert Start(dt.time(22, 0)).when_human == "at night at 22:00"
    assert Start(dt.time(23, 0)).when_human == "at night at 23:00"
