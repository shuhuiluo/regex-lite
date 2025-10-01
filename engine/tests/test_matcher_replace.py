from regex_lite.matcher import replace


def test_replace_basic():
    # Simple replacement
    result, count = replace(r"\d+", "", "abc 123 xyz 456", "#")
    assert result == "abc # xyz #"
    assert count == 2

    # No matches
    result, count = replace(r"\d+", "", "abc xyz", "#")
    assert result == "abc xyz"
    assert count == 0

    # Case insensitive
    result, count = replace("abc", "i", "ABC def ABC", "X")
    assert result == "X def X"
    assert count == 2
