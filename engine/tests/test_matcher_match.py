from regex_lite.matcher import match_spans


def test_basic_literals():
    """Test simple literal character matching."""
    
    assert match_spans("a", "banana") == [(1, 2), (3, 4), (5, 6)]
    assert match_spans("test", "this is a test string") == [(10, 14)]
    assert match_spans("x", "abc") == []  # no match


def test_dot_metacharacter():
    """Test dot (.) wildcard matching."""
    
    assert match_spans("a.c", "abc adc a-c") == [(0, 3), (4, 7), (8, 11)]
    assert match_spans(".", "ab") == [(0, 1), (1, 2)]
    # dot should not match newline by default
    assert match_spans("a.c", "a\nc", "") == []
    # dot should match newline with 's' flag
    assert match_spans("a.c", "a\nc", "s") == [(0, 3)]


def test_shorthands():
    """Test shorthand character classes \\d, \\w, \\s."""
    
    # \d matches digits
    assert match_spans(r"\d", "a1b2c3") == [(1, 2), (3, 4), (5, 6)]
    assert match_spans(r"\d+", "abc123xyz456") == [(3, 6), (9, 12)]
    # \w matches word characters
    assert match_spans(r"\w+", "hello world") == [(0, 5), (6, 11)]
    # \s matches whitespace
    assert match_spans(r"\s", "a b  c") == [(1, 2), (3, 4), (4, 5)]
    assert match_spans(r"\s+", "a b  c") == [(1, 2), (3, 5)]


def test_quantifiers():
    """Test quantifiers: *, +, ?, {m,n}."""
    
    # * (zero or more)
    assert match_spans("ab*c", "ac abc abbc") == [(0, 2), (3, 6), (7, 11)]
    # + (one or more)
    assert match_spans("ab+c", "ac abc abbc") == [(3, 6), (7, 11)]
    # ? (zero or one)
    assert match_spans("ab?c", "ac abc abbc") == [(0, 2), (3, 6)]
    # {m,n} (exact count)
    assert match_spans("a{2}", "a aa aaa") == [(2, 4), (5, 7)]
    assert match_spans("a{2,3}", "a aa aaa aaaa") == [(2, 4), (5, 8), (9, 12)]
    assert match_spans("a{2,}", "a aa aaa aaaa") == [(2, 4), (5, 8), (9, 13)]


def test_anchors():
    """Test anchors: ^ and $."""
    
    # ^ matches start of string
    assert match_spans("^abc", "abc def abc") == [(0, 3)]
    assert match_spans("^abc", "def abc") == []
    # $ matches end of string
    assert match_spans("abc$", "def abc") == [(4, 7)]
    assert match_spans("abc$", "abc def") == []
    # Both anchors
    assert match_spans("^abc$", "abc") == [(0, 3)]
    assert match_spans("^abc$", "abcd") == []  


def test_multiline_anchors():
    """Test anchors with multiline flag."""
    
    text = "abc\ndef\nghi"
    # ^ should match after newlines with 'm' flag
    assert match_spans("^def", text, "m") == [(4, 7)]
    assert match_spans("^def", text, "") == []
    # $ should match before newlines with 'm' flag
    assert match_spans("abc$", text, "m") == [(0, 3)]


def test_case_insensitive():
    """Test case-insensitive matching with 'i' flag."""
    
    assert match_spans("abc", "ABC", "i") == [(0, 3)]
    assert match_spans("AbC", "aBc", "i") == [(0, 3)]
    assert match_spans("[a-z]+", "Hello WORLD", "i") == [(0, 5), (6, 11)]


def test_complex_patterns():
    """Test more complex real-world patterns."""
    
    # Email-like pattern (simplified)
    assert match_spans(r"\w+@\w+", "user@example and admin@site") == [(0, 12), (17, 27)]
    # Phone number pattern
    assert match_spans(r"\d{3}-\d{4}", "Call 123-4567 or 987-6543") == [(5, 13), (17, 25)]
    # Word boundaries
    assert match_spans(r"\w+", "hello world 123") == [(0, 5), (6, 11), (12, 15)]
   

def test_non_overlapping_matches():
    """Test that matches don't overlap."""
    
    # Should find non-overlapping matches
    assert match_spans("ab", "ababab") == [(0, 2), (2, 4), (4, 6)]
    assert match_spans("aa", "aaaa") == [(0, 2), (2, 4)]


def test_greedy_matching():
    """Test greedy quantifier behavior."""
    
    # Greedy quantifiers should match as much as possible
    assert match_spans("a+", "aaaa") == [(0, 4)]
    assert match_spans("a*b", "aaab") == [(0, 4)]
    assert match_spans(".*", "hello") == [(0, 5), (5, 5)]


def test_alternation():
    """Test alternation (|) operator."""
    
    assert match_spans("cat|dog", "I have a cat and a dog") == [(9, 12), (19, 22)]
    assert match_spans("a|b|c", "xaxbxc") == [(1, 2), (3, 4), (5, 6)]
    # Alternation with different lengths
    assert match_spans("foo|foobar", "foo foobar") == [(0, 3), (4, 10)]
