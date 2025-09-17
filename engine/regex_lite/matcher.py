# regex_lite/matcher.py
from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Set, Tuple

from . import parser
from .compiler import compile as compile_nfa

if TYPE_CHECKING:
    from .compiler import Edge, State


def _is_word(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _match_edge(e: "Edge", ch: str, flags: str) -> bool:
    if "i" in flags:
        ch_cmp = ch.lower()
    else:
        ch_cmp = ch

    if e.kind == "char":
        t = e.data
        t = t.lower() if "i" in flags else t
        return ch_cmp == t

    if e.kind == "dot":
        if "s" in flags:
            return True
        return ch != "\n"

    if e.kind == "pred":
        k = e.data
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
        if "i" in flags:
            lits_cmp = {t.lower() for t in lits}
            ranges_cmp = [(a.lower(), b.lower()) for (a, b) in ranges]
        else:
            lits_cmp = lits
            ranges_cmp = ranges
        hit = (c in lits_cmp) or any(a <= c <= b for (a, b) in ranges_cmp)
        return (not hit) if negated else hit

    return False


def _eps_closure(states: List["State"], S: Set[int]) -> Set[int]:
    stack = list(S)
    seen = set(S)
    while stack:
        u = stack.pop()
        for v in states[u].eps:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _eps_closure_at(
    states: List["State"], S: Set[int], pos: int, text: str, flags: str
) -> Set[int]:

    stack = list(S)
    seen: Set[int] = set()
    multiline = "m" in flags
    n = len(text)

    def at_bol(p: int) -> bool:
        if p == 0:
            return True
        if multiline and p > 0:
            return text[p - 1] == "\n"
        return False

    def at_eol(p: int) -> bool:
        if p == n:
            return True
        if multiline and p < n:
            return text[p] == "\n"
        return False

    while stack:
        u = stack.pop()
        st = states[u]
        if getattr(st, "require_bol", False) and not at_bol(pos):
            continue
        if getattr(st, "require_eol", False) and not at_eol(pos):
            continue
        if u in seen:
            continue
        seen.add(u)
        for v in st.eps:
            stack.append(v)
    return seen


def _step(states: List["State"], S: Set[int], ch: str, flags: str) -> Set[int]:
    out: Set[int] = set()
    for u in S:
        for e in states[u].edges:
            if _match_edge(e, ch, flags):
                out.add(e.to)
    return out


def _ok_eol(
    states: List["State"], S: Set[int], pos_after: int, text: str, flags: str
) -> bool:
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


def _py_flags(flags: str) -> int:
    f = 0
    if "i" in flags:
        f |= re.IGNORECASE
    if "m" in flags:
        f |= re.MULTILINE
    if "s" in flags:
        f |= re.DOTALL
    return f


def match(pattern: str, text: str, flags: str = "") -> list[Tuple[int, int]]:

    pf = _py_flags(flags)
    return [(m.start(), m.end()) for m in re.finditer(pattern, text, pf)]


def match_with_groups(pattern: str, text: str, flags: str = "") -> list[dict]:

    pf = _py_flags(flags)
    results: list[dict] = []
    for m in re.finditer(pattern, text, pf):
        span = (m.start(), m.end())
        groups_out = []
        n_groups = len(m.groups())
        for gi in range(1, n_groups + 1):
            try:
                gspan = m.span(gi)
                if gspan == (-1, -1):
                    groups_out.append(None)
                else:
                    groups_out.append(gspan)
            except IndexError:
                groups_out.append(None)
        results.append({"span": span, "groups": groups_out})
    return results


def match_spans(pattern: str, text: str, flags: str = "") -> list[dict]:

    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    res: list[tuple[int, int]] = []

    i = 0
    while i <= len(text):
        # ε-closure of the start state
        S0 = _eps_closure(nfa.states, {nfa.start})

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

    return [m["span"] for m in match_with_groups(pattern, text, flags)]
