from __future__ import annotations

from dataclasses import dataclass
from typing import List


class Node:
    pass


@dataclass
class Literal(Node):
    value: str


@dataclass
class Dot(Node):
    pass


@dataclass
class Sequence(Node):
    parts: List[Node]


@dataclass
class Alternation(Node):
    left: Node
    right: Node


@dataclass
class Repeat(Node):
    expr: Node
    op: str


@dataclass
class Group(Node):
    expr: Node
