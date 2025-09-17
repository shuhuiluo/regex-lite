# engine/tests/test_engine_features.py
from regex_lite.matcher import match_spans as match


def test_alt_and_concat():
    # (ab|cd)e -> match abe / cde
    assert match("(ab|cd)e", "xxabe--cdeyy", "") == [(2, 5), (7, 10)]


def test_quantifiers_simple():
    assert match("a*", "baaac", "") == [
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


def test_anchor_alternation_semantics():
    import re

    # The issue: current implementation breaks anchor-alternation semantics
    # Pattern ^a|b should match:
    # - 'a' only at start of text (or line with 'm' flag)
    # - 'b' anywhere in the text
    # This is standard regex behavior - anchors apply only to their branch

    # Test 1: ^a|b should match 'b' anywhere, 'a' only at start
    text = "xbax"
    pattern = "^a|b"

    # Python re: correctly finds 'b' at position 1
    re_matches = [(m.start(), m.end()) for m in re.finditer(pattern, text)]
    print(f"Python re.finditer('{pattern}', '{text}'): {re_matches}")

    # Our implementation: incorrectly returns empty
    our_result = match(pattern, text, "")
    print(f"Our match('{pattern}', '{text}'): {our_result}")

    expected = [(1, 2)]  # matches 'b' at position 1
    assert (
        re_matches == expected
    ), f"Python re should match: {expected}, got {re_matches}"
    assert our_result == expected, f"Expected {expected}, got {our_result}"

    # Test 2: With multiline flag, ^ should match after \n too
    text = "xb\nabc"

    # Python re: finds 'b' at pos 1, 'a' at pos 3 (after \n)
    re_matches = [
        (m.start(), m.end()) for m in re.finditer(pattern, text, re.MULTILINE)
    ]
    print(f"Python re.finditer('{pattern}', '{text}', MULTILINE): {re_matches}")

    # Our implementation
    our_result = match(pattern, text, "m")
    print(f"Our match('{pattern}', '{text}', 'm'): {our_result}")

    expected = [(1, 2), (3, 4)]  # 'b' at pos 1, 'a' at pos 3 (after \n)
    assert (
        re_matches == expected
    ), f"Python re should match: {expected}, got {re_matches}"
    assert our_result == expected, f"Expected {expected}, got {our_result}"

    # Test 3: Ensure 'a' doesn't match in middle without ^
    text = "xax"

    # Python re: no matches ('a' not at start, no 'b')
    re_matches = [(m.start(), m.end()) for m in re.finditer(pattern, text)]
    print(f"Python re.finditer('{pattern}', '{text}'): {re_matches}")

    # Our implementation
    our_result = match(pattern, text, "")
    print(f"Our match('{pattern}', '{text}'): {our_result}")

    expected = []  # no matches ('a' not at start, no 'b')
    assert (
        re_matches == expected
    ), f"Python re should match: {expected}, got {re_matches}"
    assert our_result == expected, f"Expected {expected}, got {our_result}"
