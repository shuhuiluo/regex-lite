from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from . import ast


@dataclass
class State:
    edges: Dict[str, List[int]] = field(default_factory=dict)
    eps: List[int] = field(default_factory=list)
    accept: bool = False


@dataclass
class NFA:
    states: List[State]
    start: int
    accepts: Set[int]


def _new_state(states: List[State], accept: bool = False) -> int:
    states.append(State(accept=accept))
    return len(states) - 1


def _link_char(states: List[State], src: int, ch: str, dst: int) -> None:
    states[src].edges.setdefault(ch, []).append(dst)


def _link_eps(states: List[State], src: int, dst: int) -> None:
    states[src].eps.append(dst)


def _build(node: ast.Expr, states: List[State]) -> Tuple[int, int]:
    if isinstance(node, ast.Empty):
        s = _new_state(states)
        a = _new_state(states, True)
        _link_eps(states, s, a)
        return s, a

    if isinstance(node, ast.Literal):
        s = _new_state(states)
        a = _new_state(states, True)
        _link_char(states, s, node.char, a)
        return s, a

    if isinstance(node, ast.Concat):
        assert node.parts, "empty concat"
        s1, a1 = _build(node.parts[0], states)
        cur_start, cur_accept = s1, a1
        states[cur_accept].accept = False
        for part in node.parts[1:]:
            s2, a2 = _build(part, states)
            _link_eps(states, cur_accept, s2)
            states[cur_accept].accept = False
            cur_accept = a2
        states[cur_accept].accept = True
        return cur_start, cur_accept

    raise NotImplementedError(f"node not yet supported: {type(node).__name__}")


def compile(ast_tree: ast.Expr) -> NFA:
    """Compile AST into internal NFA representation."""
    states: List[State] = []
    start, accept = _build(ast_tree, states)
    accepts = {i for i, s in enumerate(states) if s.accept}
    return NFA(states=states, start=start, accepts=accepts)
