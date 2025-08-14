from regex_lite.lexer import tokenize
from regex_lite.tokens import TokenType


def test_digits():
    tokens = tokenize("123")
    assert [t.type for t in tokens] == [
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.CHAR,
        TokenType.EOF,
    ]


def test_dot():
    tokens = tokenize(".")
    assert [t.type for t in tokens] == [TokenType.DOT, TokenType.EOF]


def test_escape_metachar():
    tokens = tokenize("\\.")
    assert tokens[0].type == TokenType.CHAR
    assert tokens[0].value == "."
