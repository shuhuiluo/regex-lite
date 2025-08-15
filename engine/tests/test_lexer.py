import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from regex_lite.lexer import tokenize
from regex_lite.tokens import TokenType


def types(tokens):
    return [t.type for t in tokens]


def test_escape_sequence_tokens():
    tokens = tokenize("a\\.\\*\\+")
    assert types(tokens) == [
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.EOF,
    ]
    assert [t.value for t in tokens[:4]] == ["a", ".", "*", "+"]


def test_char_class_tokens():
    tokens = tokenize("[a-zA-Z_\\-]")
    assert types(tokens) == [
        TokenType.LBRACKET,
        TokenType.CHAR,
        TokenType.DASH,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.DASH,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.RBRACKET,
        TokenType.EOF,
    ]
    values = [t.value for t in tokens]
    assert values[1:9] == ["a", None, "z", "A", None, "Z", "_", "-"]


def test_char_class_escape_bracket():
    tokens = tokenize("[\\]]")
    assert types(tokens) == [
        TokenType.LBRACKET,
        TokenType.CHAR,
        TokenType.RBRACKET,
        TokenType.EOF,
    ]
    assert tokens[1].value == "]"


def test_hex_and_controls():
    tokens = tokenize("\\x41")
    assert types(tokens) == [TokenType.CHAR, TokenType.EOF]
    assert tokens[0].value == "A"

    tokens = tokenize("\\t\\n")
    assert types(tokens) == [TokenType.CHAR, TokenType.CHAR, TokenType.EOF]
    assert tokens[0].value == "\t" and tokens[1].value == "\n"
