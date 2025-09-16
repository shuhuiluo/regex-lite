

# @pytest.mark.skip(reason="matcher not implemented")
def test_matcher_smoke():
    from regex_lite.matcher import match

    assert match("ab", "xxabyyab") == [(2, 4), (6, 8)]
