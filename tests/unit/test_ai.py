from similarium.ai import _fix_openai_response


def test_fix_openai_response_fixes_incorrect_user_id_tags():
    assert _fix_openai_response("Hello @ABCD1234") == "Hello <@ABCD1234>"
    assert _fix_openai_response("Hello @ABCD1234!") == "Hello <@ABCD1234>!"
    assert _fix_openai_response("Hello <@ABCD1234>") == "Hello <@ABCD1234>"

    # It should fix every incorrect instance
    assert (
        _fix_openai_response("Hello @ABCD1234 @EFGH5678")
        == "Hello <@ABCD1234> <@EFGH5678>"
    )

    # It should fix only incorrect instances in mixed content
    assert (
        _fix_openai_response("Hello @ABCD1234 and <@EFGH5678>!")
        == "Hello <@ABCD1234> and <@EFGH5678>!"
    )

def test_fix_openai_response_removes_extra_quotes_around_the_content():
    assert _fix_openai_response('"Hello"') == "Hello"
