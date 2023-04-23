from similarium.ai import _fix_openai_response


def test_fix_openai_response_fixes_incorrect_user_id_tags():
    assert _fix_openai_response("Hello @UABCD1234") == "Hello <@UABCD1234>"
    assert _fix_openai_response("Hello @UABCD1234!") == "Hello <@UABCD1234>!"
    assert _fix_openai_response("Hello <@UABCD1234>") == "Hello <@UABCD1234>"
    assert _fix_openai_response("Hello UABCD1234") == "Hello <@UABCD1234>"

    # It should fix every incorrect instance
    assert (
        _fix_openai_response("Hello @UABCD1234 @UEFGH5678")
        == "Hello <@UABCD1234> <@UEFGH5678>"
    )

    # It should fix only incorrect instances in mixed content
    assert (
        _fix_openai_response("Hello @UABCD1234 and <@UEFGH5678>!")
        == "Hello <@UABCD1234> and <@UEFGH5678>!"
    )

def test_fix_openai_response_removes_extra_quotes_around_the_content():
    assert _fix_openai_response('"Hello"') == "Hello"
