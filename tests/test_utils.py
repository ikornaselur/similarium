import pytest

from semantle_slack_bot.utils import get_custom_progress_bar


def test_get_custom_progress_bar_no_progress() -> None:
    assert get_custom_progress_bar(0, 100, 8) == ":p0:" * 8
    assert get_custom_progress_bar(0, 100, 4) == ":p0:" * 4


def test_get_custom_progress_bar_full_progress() -> None:
    assert get_custom_progress_bar(100, 100, 8) == ":p8:" * 8
    assert get_custom_progress_bar(100, 100, 4) == ":p8:" * 4


def test_get_custom_progress_bar_no_width() -> None:
    with pytest.raises(ValueError, match="Width needs to be at least 1"):
        get_custom_progress_bar(0, 100, 0)


def test_get_custom_progress_bar_each_emoji() -> None:
    checks = [
        (":p0:", range(0, 16)),
        (":p1:", range(16, 32)),
        (":p2:", range(32, 48)),
        (":p3:", range(48, 64)),
        (":p4:", range(64, 80)),
        (":p5:", range(80, 96)),
        (":p6:", range(96, 112)),
        (":p7:", range(112, 128)),
        (":p8:", range(128, 129)),
    ]
    for emoji, _range in checks:
        for i in _range:
            assert get_custom_progress_bar(i, 128, 1) == emoji, f"{emoji=} {i=}"


def test_get_custom_progress_bar_over_multiple_emojis() -> None:
    assert get_custom_progress_bar(0, 16, 2) == ":p0::p0:"
    assert get_custom_progress_bar(1, 16, 2) == ":p1::p0:"
    assert get_custom_progress_bar(2, 16, 2) == ":p2::p0:"
    assert get_custom_progress_bar(3, 16, 2) == ":p3::p0:"
    assert get_custom_progress_bar(4, 16, 2) == ":p4::p0:"
    assert get_custom_progress_bar(5, 16, 2) == ":p5::p0:"
    assert get_custom_progress_bar(6, 16, 2) == ":p6::p0:"
    assert get_custom_progress_bar(7, 16, 2) == ":p7::p0:"
    assert get_custom_progress_bar(8, 16, 2) == ":p8::p0:"
    assert get_custom_progress_bar(9, 16, 2) == ":p8::p1:"
    assert get_custom_progress_bar(10, 16, 2) == ":p8::p2:"
    assert get_custom_progress_bar(11, 16, 2) == ":p8::p3:"
    assert get_custom_progress_bar(12, 16, 2) == ":p8::p4:"
    assert get_custom_progress_bar(13, 16, 2) == ":p8::p5:"
    assert get_custom_progress_bar(14, 16, 2) == ":p8::p6:"
    assert get_custom_progress_bar(15, 16, 2) == ":p8::p7:"
    assert get_custom_progress_bar(16, 16, 2) == ":p8::p8:"


def test_get_custom_progress_bar_longer() -> None:
    assert get_custom_progress_bar(7, 128, 8) == ":p3::p0::p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(23, 128, 8) == ":p8::p3::p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(33, 128, 8) == ":p8::p8::p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(85, 128, 8) == ":p8::p8::p8::p8::p8::p2::p0::p0:"
    assert get_custom_progress_bar(91, 128, 8) == ":p8::p8::p8::p8::p8::p5::p0::p0:"
    assert get_custom_progress_bar(127, 128, 8) == ":p8::p8::p8::p8::p8::p8::p8::p7:"
    assert get_custom_progress_bar(128, 128, 8) == ":p8::p8::p8::p8::p8::p8::p8::p8:"
