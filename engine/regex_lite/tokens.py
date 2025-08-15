from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Enumeration of lexer token types."""

    # Literals and special atoms
    CHAR = auto()  # literal character
    DOT = auto()  # .
    CARET = auto()  # ^ anchor
    DOLLAR = auto()  # $ anchor
    SHORTHAND = auto()  # \d, \w, etc.

    # Operators / metacharacters
    STAR = auto()
    PLUS = auto()
    QUESTION = auto()
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    PIPE = auto()
    DASH = auto()
    COMMA = auto()

    EOF = auto()


@dataclass
class Token:
    """Token with optional value and original position."""

    type: TokenType
    value: str | None = None
    pos: int | None = None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        if self.value is not None:
            return f"Token({self.type}, {self.value!r}, pos={self.pos})"
        return f"Token({self.type}, pos={self.pos})"
