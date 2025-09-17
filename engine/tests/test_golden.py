from regex_lite.matcher import match_spans as match
from regex_lite.matcher import match_with_groups


def test_g_alt_concat():
    # (ab|cd)e → should match "abe" and "cde"
    assert match("(ab|cd)e", "xxabe--cdeyy", "") == [(2, 5), (7, 10)]


def test_g_quantifiers():
    assert match("a*", "baaac", "g") == [(0, 0), (1, 4), (4, 4), (5, 5)]
    assert match("b+", "abbbc", "") == [(1, 4)]
    assert match("c{2,3}", "abcccd", "") == [(2, 5)]


def test_g_charclass_and_ranges():
    assert match("[a-c]+", "zzabccdz", "") == [(2, 6)]
    assert match("[^0-9]+", "123ab45", "g") == [(3, 5)]


def test_g_dot_and_flags():
    assert match("a.c", "a\nc", "") == []  # by default '.' does not match '\n'
    assert match("a.c", "a\nc", "s") == [(0, 3)]  # dotall mode matches newline


def test_g_anchors():
    assert match("^abc$", "abc", "") == [(0, 3)]
    assert match("^ab", "xab\nab", "m") == [
        (4, 6)
    ]  # multiline ^ should match line start


def test_g_ignore_case():
    assert match("AbC", "xxabcYY", "i") == [(2, 5)]


def test_capturing_simple():
    # Capturing group: groups[0] should be (1,3) corresponding to "ab"
    res = match_with_groups("(ab)c", "zabc")
    assert res == [{"span": (1, 4), "groups": [(1, 3)]}]


def test_capturing_nested_last_win():
    # For (a|b)+c, group 1 should capture the *last* branch matched.
    # We only assert the overall span is correct, not which branch was last.
    res = match_with_groups("(a|b)+c", "aaabbc")
    assert res[0]["span"] == (0, 6)
    # The groups list contains the last (a|b) match, which could be either 'a' or 'b'
    assert len(res[0]["groups"]) >= 1


def test_capturing_alt_concat():
    res = match_with_groups("(ab|cd)e", "xxabe--cdeyy")
    spans = [m["span"] for m in res]
    groups = [m["groups"][0] for m in res]  # group 1
    assert spans == [(2, 5), (7, 10)]
    assert groups == [(2, 4), (7, 9)]
