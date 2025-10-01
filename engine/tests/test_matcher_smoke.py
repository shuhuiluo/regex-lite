# @pytest.mark.skip(reason="matcher not implemented")
def test_matcher_smoke():
    from regex_lite.matcher import match, match_spans

    assert match_spans("ab", "xxabyyab") == [(2, 4), (6, 8)]
    # zero-length producer shouldn't loop; matches at every position boundary
    assert match_spans("a*", "b") == [(0, 0), (1, 1)]
    assert match("^a|b", "xbax", "") == [(1, 2)]
    assert match(r"\d+", "abc 123 xyz", "") == [(4, 7)]  
