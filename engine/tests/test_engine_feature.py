# engine/tests/test_engine_features.py
from regex_lite.matcher import match


def test_alt_and_concat():
    # (ab|cd)e -> match abe / cde
    assert match("(ab|cd)e", "xxabe--cdeyy", "") == [(2, 5), (7, 10)]


def test_quantifiers_simple():
    assert match("a*", "baaac", "g") == [
        (0, 0),
        (1, 4),
        (4, 4),
        (5, 5),
    ]
    assert match("b+", "abbbc", "") == [(1, 4)]
    assert match("c{2,3}", "abcccd", "") == [(2, 5)]


def test_charclass_and_ranges():
    assert match("[a-c]+", "zzabccdz", "") == [(2, 6)]
    assert match("[^0-9]+", "123ab45", "g") == [(3, 5)]


def test_dot_and_flags():
    assert match("a.c", "a\nc", "") == []
    assert match("a.c", "a\nc", "s") == [(0, 3)]  # dotall


def test_anchors():
    assert match("^abc$", "abc", "") == [(0, 3)]
    assert match("^ab", "xab\nab", "m") == [(4, 6)]


def test_ignore_case():
    assert match("AbC", "xxabcYY", "i") == [(2, 5)]
