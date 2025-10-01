from regex_lite.matcher import split


def test_split_basic():
    # Simple split
    pieces = split(r" ", "a b c", "")
    assert pieces == ["a", "b", "c"]

    # Multiple spaces
    pieces = split(r"\s+", "a  b   c", "")
    assert pieces == ["a", "b", "c"]

    # No matches
    pieces = split(r"\d+", "abc", "")
    assert pieces == ["abc"]

    # Pattern at edges
    pieces = split(r"\s+", "  a b  ", "")
    assert pieces == ["", "a", "b", ""]
