from __future__ import annotations

from typing import TYPE_CHECKING, List, Set

from . import parser
from .compiler import compile as compile_nfa

if TYPE_CHECKING:
    from .compiler import Edge, State


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
        if "i" in flags:
            lits_cmp = {t.lower() for t in lits}
            ranges_cmp = [(a.lower(), b.lower()) for (a, b) in ranges]
        else:
            lits_cmp = lits
            ranges_cmp = ranges
        hit = (c in lits_cmp) or any(a <= c <= b for (a, b) in ranges_cmp)
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


def _eps_closure_at(
    states: List["State"], S: Set[int], pos: int, text: str, flags: str
) -> Set[int]:
    """
    +    Position-aware ε-closure that respects ^/$ anchors on the fly.
    +    Assume State has fields: eps (list[int]), bol (bool), eol (bool).
    +"""
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
        # enforce anchors on this node, if present
        # enforce anchors on this node, if present
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
        # S0 = _eps_closure(nfa.states, {nfa.start})
        S0 = _eps_closure_at(nfa.states, {nfa.start}, i, text, flags)
        # Check start-anchor (^) at current position
        # if not _ok_bol(nfa.states, S0, i, text, flags):
        #    i += 1
        #    continue

        # Greedy search: record the longest accepted j
        S = set(S0)
        j = i
        best_j = None

        # Acceptable from the start (empty match / pure anchor)
        # Sc = _eps_closure(nfa.states, S)
        Sc = _eps_closure_at(nfa.states, S, j, text, flags)
        if any(nfa.states[s].accept for s in Sc) and _ok_eol(
            nfa.states, Sc, j, text, flags
        ):
            best_j = j

        # Consume characters to find the longest match
        while j < len(text):
            Sc = _eps_closure_at(nfa.states, S, j, text, flags)
            S = _step(nfa.states, Sc, text[j], flags)
            if not S:
                break
            j += 1
            Sc2 = _eps_closure_at(nfa.states, S, j, text, flags)
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

    # return match_with_groups(pattern, text, flags)
    return res


def match_with_groups(pattern: str, text: str, flags: str = "") -> list[dict]:
    """
    Return a list of dictionaries like:
    [
      {"span": (start, end), "groups": [(g1_start, g1_end) | None, (g2_start, g2_end) | None, ...]},
      ...
    ]
    Group indices follow the order of parentheses ( ... ), starting from 1.
    If a group does not match, its entry will be None.
    """
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    results: list[dict] = []

    i = 0
    while i <= len(text):
        # Starting state ε-closure
        S0 = _eps_closure(nfa.states, {nfa.start})

        # Start-anchor (^) check at current position
        # if not _ok_bol(nfa.states, S0, i, text, flags):
        #    i += 1
        #    continue

        # --- Capture group tracking (reused within this iteration for current i) ---
        group_starts: dict[int, int] = {}
        group_spans: dict[int, tuple[int, int]] = {}

        def _apply_group_hooks(state_set: set[int], pos: int):
            # Record group start/end based on enter/exit hooks
            for s in state_set:
                st = nfa.states[s]
                # Entering a group: record its start position
                for g in st.enter_groups:
                    group_starts[g] = pos
                # Exiting a group: if we have a start, record the span
                for g in st.exit_groups:
                    start = group_starts.get(g)
                    if start is not None:
                        group_spans[g] = (start, pos)

        # Greedy search: record the longest accepted j and its groups
        S = set(S0)
        j = i
        best_j: int | None = None
        best_groups: dict[int, tuple[int, int]] | None = None

        # Apply group hooks on initial ε-closure
        Sc = _eps_closure(nfa.states, S)
        _apply_group_hooks(Sc, j)

        # Acceptable at start (empty match / pure anchors)
        if any(nfa.states[s].accept for s in Sc) and _ok_eol(
            nfa.states, Sc, j, text, flags
        ):
            best_j = j
            best_groups = dict(group_spans)

        # Consume characters to find the longest match
        while j < len(text):
            Sc = _eps_closure(nfa.states, S)
            S = _step(nfa.states, Sc, text[j], flags)
            if not S:
                break
            j += 1
            Sc2 = _eps_closure(nfa.states, S)
            _apply_group_hooks(Sc2, j)
            if any(nfa.states[s].accept for s in Sc2) and _ok_eol(
                nfa.states, Sc2, j, text, flags
            ):
                best_j = j
                best_groups = dict(group_spans)

        if best_j is not None:
            # Normalize groups: fill from 1..max_index, use None for missing groups
            max_idx = max(best_groups.keys(), default=0) if best_groups else 0
            ordered_groups = [None] * max_idx
            if best_groups:
                for k, span in best_groups.items():
                    if k >= 1:
                        # Expand defensively if needed (rare)
                        if k > len(ordered_groups):
                            ordered_groups.extend([None] * (k - len(ordered_groups)))
                        ordered_groups[k - 1] = span
            results.append({"span": (i, best_j), "groups": ordered_groups})
            # Avoid infinite loop on zero-length matches
            i = best_j if best_j > i else i + 1
        else:
            i += 1

    return results


def match_spans(pattern: str, text: str, flags: str = "") -> list[dict]:
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    res: list[tuple[int, int]] = []

    i = 0
    while i <= len(text):
        # ε-closure of the start state
        S0 = _eps_closure(nfa.states, {nfa.start})

        # Check start-anchor (^) at current position
        # if not _ok_bol(nfa.states, S0, i, text, flags):
        #    i += 1
        #    continue

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
