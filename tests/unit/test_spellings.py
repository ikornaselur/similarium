from similarium.spellings import americanize


def test_americanize_falls_back_if_spelling_not_found():
    word = "foobar"

    assert americanize(word) == word


def test_americanize_returns_american_spelling_for_british_word():
    british = "accessorise"
    american = "accessorize"

    assert americanize(british) == american
