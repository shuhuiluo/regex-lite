from __future__ import annotations

import warnings
from typing import List

from .tokens import Token, TokenType

_HEX_DIGITS = "0123456789abcdefABCDEF"
_ESCAPABLE = ".*+?|()[]{}^$\\"
_SHORTHANDS = "dDwWsS"


class Lexer:
    """Simple lexer for the regex language.

    It performs a single left-to-right pass and emits :class:`Token` objects
    annotated with their position in the original pattern.  The lexer itself is
    purposely small – validation of constructs is largely deferred to the
    parser.
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.length = len(pattern)
        self.i = 0
        self.in_class = False

    # ------------------------------------------------------------------
    # core utilities
    def _current(self) -> str:
        return self.pattern[self.i]

    def _advance(self, n: int = 1) -> None:
        self.i += n

    def _eof(self) -> bool:
        return self.i >= self.length

    # ------------------------------------------------------------------
    def tokenize(self) -> List[Token]:
        """Tokenize ``pattern`` into a flat list of :class:`Token` objects.

        The lexer keeps track of whether it is currently inside a character
        class (``[...]``) so that it can interpret characters like ``-`` or
        ``^`` appropriately.  Aside from escape handling, the lexer performs no
        validation; errors are reported by the parser.
        """

        tokens: List[Token] = []
        while not self._eof():
            pos = self.i
            ch = self._current()
            if self.in_class:
                token, value = self._lex_class_char(pos, ch)
            else:
                token, value = self._lex_regular_char(pos, ch)
            tokens.append(Token(token, value, pos))
            if token == TokenType.LBRACKET:
                self.in_class = True
            elif token == TokenType.RBRACKET:
                self.in_class = False
        tokens.append(Token(TokenType.EOF, pos=self.i))
        return tokens

    # ------------------------------------------------------------------
    def _read_escape(self, pos: int, in_class: bool) -> tuple[TokenType, str | None]:
        """Handle escape sequences starting after the backslash."""

        if self._eof():
            raise ValueError("dangling escape")
        ch = self._current()
        self._advance()
        if ch in "tnr":
            mapping = {"t": "\t", "n": "\n", "r": "\r"}
            return TokenType.CHAR, mapping[ch]
        if ch == "x":
            if self.i + 1 >= self.length:
                raise ValueError("incomplete hex escape")
            hex_digits = self.pattern[self.i : self.i + 2]
            if any(c not in _HEX_DIGITS for c in hex_digits):
                raise ValueError("invalid hex escape")
            self._advance(2)
            return TokenType.CHAR, chr(int(hex_digits, 16))
        if ch in _SHORTHANDS:
            return TokenType.SHORTHAND, ch
        if ch in _ESCAPABLE or (in_class and ch in "-]"):
            return TokenType.CHAR, ch
        # Unknown escape -> literal character
        warnings.warn(
            f"Unknown escape sequence '\\{ch}' at position {pos} is treated as a literal character. "
            "This may not match standard regex behavior.",
            UserWarning,
        )
        return TokenType.CHAR, ch

    def _lex_regular_char(self, pos: int, ch: str) -> tuple[TokenType, str | None]:
        """Lex a character outside of a character class."""

        self._advance()
        if ch == "\\":
            token, value = self._read_escape(pos + 1, False)
            return token, value
        if ch == ".":
            return TokenType.DOT, None
        if ch == "*":
            return TokenType.STAR, None
        if ch == "+":
            return TokenType.PLUS, None
        if ch == "?":
            return TokenType.QUESTION, None
        if ch == "(":
            return TokenType.LPAREN, None
        if ch == ")":
            return TokenType.RPAREN, None
        if ch == "[":
            return TokenType.LBRACKET, None
        if ch == "]":
            return TokenType.RBRACKET, None
        if ch == "{":
            return TokenType.LBRACE, None
        if ch == "}":
            return TokenType.RBRACE, None
        if ch == "|":
            return TokenType.PIPE, None
        if ch == "^":
            return TokenType.CARET, None
        if ch == "$":
            return TokenType.DOLLAR, None
        if ch == "-":
            # outside char class hyphen is literal
            return TokenType.CHAR, "-"
        if ch == ",":
            return TokenType.COMMA, None
        return TokenType.CHAR, ch

    def _lex_class_char(self, pos: int, ch: str) -> tuple[TokenType, str | None]:
        """Lex a character appearing inside a ``[...]`` character class."""

        self._advance()
        if ch == "\\":
            return self._read_escape(pos + 1, True)
        if ch == "]":
            return TokenType.RBRACKET, None
        if ch == "-":
            return TokenType.DASH, None
        # caret has special meaning only in first position which parser handles
        if ch == "^":
            return TokenType.CARET, None
        return TokenType.CHAR, ch


def tokenize(pattern: str) -> List[Token]:
    """Tokenize ``pattern`` using :class:`Lexer`.

    This is a thin convenience wrapper used by the parser and tests.
    """

    return Lexer(pattern).tokenize()
