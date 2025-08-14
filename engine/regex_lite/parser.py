from __future__ import annotations

from . import ast


def parse(pattern: str) -> ast.Node:
    """Parse pattern into an AST."""
    raise NotImplementedError("Parser not implemented")
