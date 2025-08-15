from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


class Expr:
    """Base class for all AST nodes."""


@dataclass
class Literal(Expr):
    char: str


@dataclass
class Dot(Expr):
    pass


@dataclass
class AnchorStart(Expr):
    pass


@dataclass
class AnchorEnd(Expr):
    pass


@dataclass
class Shorthand(Expr):
    kind: str  # 'd','D','w','W','s','S'


@dataclass
class Range:
    start: str
    end: str


ClassItem = Union[Literal, Range, Shorthand]


@dataclass
class CharClass(Expr):
    items: List[ClassItem]
    negated: bool = False


@dataclass
class Group(Expr):
    expr: Expr
    index: int


@dataclass
class Concat(Expr):
    parts: List[Expr]


@dataclass
class Alt(Expr):
    options: List[Expr]


@dataclass
class Repeat(Expr):
    expr: Expr
    kind: str  # '*', '+', '?', '{m}', '{m,}', '{m,n}'
    m: int | None = None
    n: int | None = None

