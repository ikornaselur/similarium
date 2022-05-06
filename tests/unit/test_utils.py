import pytest

from similarium.utils import cos_sim, get_custom_progress_bar, get_secret


def test_get_custom_progress_bar_no_progress() -> None:
    assert get_custom_progress_bar(0, 100, 8) == ":p0:" * 8
    assert get_custom_progress_bar(0, 100, 4) == ":p0:" * 4


def test_get_custom_progress_bar_full_progress() -> None:
    assert get_custom_progress_bar(100, 100, 8) == ":p8:" * 8
    assert get_custom_progress_bar(100, 100, 4) == ":p8:" * 4


def test_get_custom_progress_bar_no_width() -> None:
    with pytest.raises(ValueError, match="Width needs to be at least 1"):
        get_custom_progress_bar(0, 100, 0)


def test_get_custom_progress_bar_base_cases() -> None:
    assert get_custom_progress_bar(0, 8, 1) == ":p0:"
    assert get_custom_progress_bar(1, 8, 1) == ":p1:"
    assert get_custom_progress_bar(2, 8, 1) == ":p2:"
    assert get_custom_progress_bar(3, 8, 1) == ":p3:"
    assert get_custom_progress_bar(4, 8, 1) == ":p4:"
    assert get_custom_progress_bar(5, 8, 1) == ":p5:"
    assert get_custom_progress_bar(6, 8, 1) == ":p6:"
    assert get_custom_progress_bar(7, 8, 1) == ":p7:"
    assert get_custom_progress_bar(8, 8, 1) == ":p8:"


def test_get_custom_progress_bar_base_cases_larger_total() -> None:
    """
    For a total of 22, with width 1, each section (except the last)
    should last 3 "units".
    This means:
        * 1-7 are represented thrice (3*7)
        * 8 is represente once (1)
    for a total of 3*7 + 1 = 22
    """
    total = 22

    checks = [
        (":p0:", [0]),
        (":p1:", [1, 2, 3]),
        (":p2:", [4, 5, 6]),
        (":p3:", [7, 8, 9]),
        (":p4:", [10, 11, 12]),
        (":p5:", [13, 14, 15]),
        (":p6:", [16, 17, 18]),
        (":p7:", [19, 20, 21]),
        (":p8:", [22]),
    ]

    for emoji, _range in checks:
        for i in _range:
            assert get_custom_progress_bar(i, total, 1) == emoji, f"{emoji=} {i=}"


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
    assert get_custom_progress_bar(7, 128, 8) == ":p4::p0::p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(23, 128, 8) == ":p8::p4::p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(33, 128, 8) == ":p8::p8::p1::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(85, 128, 8) == ":p8::p8::p8::p8::p8::p3::p0::p0:"
    assert get_custom_progress_bar(91, 128, 8) == ":p8::p8::p8::p8::p8::p6::p0::p0:"
    assert get_custom_progress_bar(127, 128, 8) == ":p8::p8::p8::p8::p8::p8::p8::p7:"
    assert get_custom_progress_bar(128, 128, 8) == ":p8::p8::p8::p8::p8::p8::p8::p8:"


def test_get_custom_progress_bar_immediately_shows_progress() -> None:
    assert get_custom_progress_bar(0, 1000, 4) == ":p0::p0::p0::p0:"
    assert get_custom_progress_bar(1, 1000, 4) == ":p1::p0::p0::p0:"


def test_get_custom_progress_bar_only_shows_complete_if_full() -> None:
    assert get_custom_progress_bar(999, 1000, 4) == ":p8::p8::p8::p7:"
    assert get_custom_progress_bar(1000, 1000, 4) == ":p8::p8::p8::p8:"


def test_get_custom_progress_bar_issue1() -> None:
    assert get_custom_progress_bar(0, 1000, 6) == ":p0::p0::p0::p0::p0::p0:"
    assert get_custom_progress_bar(998, 1000, 6) == ":p8::p8::p8::p8::p8::p7:"
    assert get_custom_progress_bar(1000, 1000, 6) == ":p8::p8::p8::p8::p8::p8:"


def test_get_custom_progress_bar_width_is_always_correct() -> None:
    total = 100
    for units in range(0, total + 1):
        for width in range(1, 10):
            expected_width = width * 4  # Each emoji is 4 characters
            assert len(get_custom_progress_bar(units, total, width)) == expected_width


def test_get_secret_is_consistent_for_input() -> None:
    secret = get_secret(channel="foo", day=1)

    assert get_secret(channel="foo", day=1) == secret


def test_get_secret_is_different_for_different_channels() -> None:
    secret = get_secret(channel="chan_1", day=1)

    assert get_secret(channel="chan_2", day=1) != secret


def test_get_secret_is_different_for_different_day() -> None:
    secret = get_secret(channel="foo", day=1)

    assert secret != get_secret(channel="foo", day=2)


def test_cos_sim() -> None:
    assert cos_sim([1, 2], [3, 4]) == pytest.approx(0.9838699100999074)
    assert cos_sim([3, 4], [1, 2]) == pytest.approx(0.9838699100999074)
