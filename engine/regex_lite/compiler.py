from __future__ import annotations

from . import ast


def compile(ast_tree: ast.Node) -> object:
    """Compile AST into internal NFA representation."""
    raise NotImplementedError("Compiler not implemented")
