import pytest

from similarium import celebration
from similarium.celebration import CelebrationType, get_celebration_message


@pytest.mark.parametrize(
    "celebration_list, celebration_type",
    [
        ("celebration_messages_top_10", "TOP_10"),
        ("celebration_messages_top_100", "TOP_100"),
        ("celebration_messages_top_1000", "TOP_1000"),
        ("celebration_messages_top_10_first_guess", "TOP_10_FIRST"),
        ("celebration_messages_top_1000_first_guess", "TOP_1000_FIRST"),
    ],
)
def test_celebration_messages(
    celebration_list: str, celebration_type: str, monkeypatch
) -> None:
    celebration_list = getattr(celebration, celebration_list)
    message_count = len(celebration_list)

    idx = 0

    def _choice(lst):
        nonlocal idx

        if lst == celebration_list:
            elm = lst[idx]
            idx += 1
            return elm

        return lst[0]

    monkeypatch.setattr("random.choice", _choice)

    messages = set()
    for _ in range(message_count):
        message = get_celebration_message(
            CelebrationType(celebration_type), "user_x", "the_word"
        )
        messages.add(message)

    # Assert that the unique generated messages are the same count as the templates
    assert len(messages) == message_count

    # Assert that each of them mentions the user_id and the word
    for message in messages:
        assert "<@user_x>" in message
        assert "`the_word`" in message
