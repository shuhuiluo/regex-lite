from __future__ import annotations

from typing import List, Set

from . import parser
from .compiler import Edge, State
from .compiler import compile as compile_nfa


def _is_word(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _match_edge(e: Edge, ch: str, flags: str) -> bool:
    # i: ignore case
    if "i" in flags:
        ch_cmp = ch.lower()
    else:
        ch_cmp = ch

    if e.kind == "char":
        t = e.data
        t = t.lower() if "i" in flags else t
        return ch_cmp == t

    if e.kind == "dot":
        # s: dotall -> '.' can match '\n'
        if "s" in flags:
            return True
        return ch != "\n"

    if e.kind == "pred":
        k = e.data  # 'd'|'w'|'s'
        if k == "d":
            return ch.isdigit()
        if k == "w":
            return _is_word(ch)
        if k == "s":
            return ch.isspace()
        return False

    if e.kind == "class":
        negated, lits, ranges = e.data
        c = ch_cmp
        hit = (c in lits) or any(r[0] <= c <= r[1] for r in ranges)
        return (not hit) if negated else hit

    return False


def _eps_closure(states: List[State], S: Set[int]) -> Set[int]:
    stack = list(S)
    seen = set(S)
    while stack:
        u = stack.pop()
        for v in states[u].eps:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _step(states: List[State], S: Set[int], ch: str, flags: str) -> Set[int]:
    out: Set[int] = set()
    for u in S:
        for e in states[u].edges:
            if _match_edge(e, ch, flags):
                out.add(e.to)
    return out


def _ok_bol(states: List[State], S: Set[int], pos: int, text: str, flags: str) -> bool:
    # States with require_bol can only be entered at the start of a line/text
    for u in S:
        if states[u].require_bol:
            if "m" in flags:
                if not (pos == 0 or text[pos - 1] == "\n"):
                    return False
            else:
                if pos != 0:
                    return False
    return True


def _ok_eol(
    states: List[State], S: Set[int], pos_after: int, text: str, flags: str
) -> bool:
    # States with require_eol must be at line end/text end
    for u in S:
        if states[u].require_eol:
            if "m" in flags:
                if not (
                    pos_after == len(text)
                    or (pos_after < len(text) and text[pos_after] == "\n")
                ):
                    return False
            else:
                if pos_after != len(text):
                    return False
    return True


def match(pattern: str, text: str, flags: str = "") -> list[tuple[int, int]]:
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    res: list[tuple[int, int]] = []

    i = 0
    while i <= len(text):
        # ε-closure of the start state
        S0 = _eps_closure(nfa.states, {nfa.start})

        # Check start-anchor (^) at current position
        if not _ok_bol(nfa.states, S0, i, text, flags):
            i += 1
            continue

        # Greedy search: record the longest accepted j
        S = set(S0)
        j = i
        best_j = None

        # Acceptable from the start (empty match / pure anchor)
        Sc = _eps_closure(nfa.states, S)
        if any(nfa.states[s].accept for s in Sc) and _ok_eol(
            nfa.states, Sc, j, text, flags
        ):
            best_j = j

        # Consume characters to find the longest match
        while j < len(text):
            Sc = _eps_closure(nfa.states, S)
            S = _step(nfa.states, Sc, text[j], flags)
            if not S:
                break
            j += 1
            Sc2 = _eps_closure(nfa.states, S)
            if any(nfa.states[s].accept for s in Sc2) and _ok_eol(
                nfa.states, Sc2, j, text, flags
            ):
                best_j = j

        # If any accepted position found, record the longest one
        if best_j is not None:
            res.append((i, best_j))
            # Avoid zero-length infinite loop: advance at least 1 char
            i = best_j if best_j > i else i + 1
        else:
            i += 1

    return res
