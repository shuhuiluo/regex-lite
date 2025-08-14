from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    CHAR = auto()
    DOT = auto()
    STAR = auto()
    PLUS = auto()
    QUESTION = auto()
    LPAREN = auto()
    RPAREN = auto()
    PIPE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str | None = None
