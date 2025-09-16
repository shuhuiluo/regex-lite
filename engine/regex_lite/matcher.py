from __future__ import annotations

from typing import List, Set

from . import parser
from .compiler import compile as compile_nfa


def _eps_closure(states, S: Set[int]) -> Set[int]:
    stack = list(S)
    seen = set(S)
    while stack:
        u = stack.pop()
        for v in states[u].eps:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _step(states, S: Set[int], ch: str) -> Set[int]:
    out: Set[int] = set()
    for u in S:
        for v in states[u].edges.get(ch, []):
            out.add(v)
    return out


def match(pattern: str, text: str, flags: str = "") -> list[tuple[int, int]]:
    """Stub matcher that will eventually simulate the NFA."""
    # raise NotImplementedError("Matcher not implemented")
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    res: List[tuple[int, int]] = []

    for i in range(len(text) + 1):
        S = _eps_closure(nfa.states, {nfa.start})
        j = i
        while j < len(text):
            S = _step(nfa.states, S, text[j])
            if not S:
                break
            S = _eps_closure(nfa.states, S)
            j += 1
            if any(nfa.states[s].accept for s in S):
                res.append((i, j))
                break
    return res
