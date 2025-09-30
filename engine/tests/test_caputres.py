def test_capturing_groups():
    from regex_lite.matcher import match_with_groups

    res = match_with_groups("(ab)c", "zabc")
    assert res[0]["span"] == (1, 4)
    assert res[0]["groups"][0] == (1, 3)
