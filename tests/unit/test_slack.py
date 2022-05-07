from unittest import mock

from similarium.slack import _idx


def test_slack_idx_under_10() -> None:
    for i in range(1, 10):
        num, spaces = _idx(mock.Mock(idx=i)).split(".")
        assert num == str(i)
        assert len(spaces) == 6


def test_slack_idx_between_10_and_100() -> None:
    for i in range(10, 100, 10):
        num, spaces = _idx(mock.Mock(idx=i)).split(".")
        assert num == str(i)
        assert len(spaces) == 4


def test_slack_idx_between_100_and_1000() -> None:
    for i in range(100, 200, 10):
        num, spaces = _idx(mock.Mock(idx=i)).split(".")
        assert num == str(i)
        assert len(spaces) == 2
