from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


class Expr:
    """Base class for all AST nodes."""


@dataclass
class Literal(Expr):
    """Single literal character, e.g. ``a`` in ``a+``."""

    char: str


@dataclass
class Dot(Expr):
    """Wildcard ``.`` that matches any character."""


@dataclass
class AnchorStart(Expr):
    """Beginning-of-string anchor ``^``."""


@dataclass
class AnchorEnd(Expr):
    """End-of-string anchor ``$``."""


@dataclass
class Shorthand(Expr):
    r"""Shorthand character classes like ``\d`` or ``\w``."""

    kind: str  # 'd','D','w','W','s','S'


@dataclass
class Range:
    """Character range ``a-z`` inside a character class."""

    start: str
    end: str


ClassItem = Union[Literal, Range, Shorthand]


@dataclass
class CharClass(Expr):
    """Character class, e.g. ``[a-z]`` or ``[^0-9]``."""

    items: List[ClassItem]
    negated: bool = False


@dataclass
class Group(Expr):
    """Capturing group ``( ... )`` with 1-based ``index``."""

    expr: Expr
    index: int


@dataclass
class Concat(Expr):
    """Sequence of expressions concatenated together, e.g. ``ab``."""

    parts: List[Expr]


@dataclass
class Alt(Expr):
    """Alternation ``a|b`` between multiple ``options``."""

    options: List[Expr]


@dataclass
class Repeat(Expr):
    """Quantifier like ``*`` or ``{m,n}`` applying to ``expr``."""

    expr: Expr
    kind: str  # '*', '+', '?', '{m}', '{m,}', '{m,n}'
    m: int | None = None
    n: int | None = None
