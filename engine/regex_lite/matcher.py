# regex_lite/matcher.py
from __future__ import annotations

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


# --- Position-aware ε-closure: check require_bol/require_eol at current pos ---
def _eps_closure_at(
    states: List["State"], S: Set[int], pos: int, text: str, flags: str
) -> Set[int]:
    stack = list(S)
    seen: Set[int] = set()
    n = len(text)
    multiline = "m" in flags

    def at_bol(p: int) -> bool:
        if p == 0:
            return True
        return multiline and text[p - 1] == "\n"

    def at_eol(p: int) -> bool:
        if p == n:
            return True
        return multiline and text[p] == "\n"

    while stack:
        u = stack.pop()
        st = states[u]
        # Enforce anchor checks at current position
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


# --- Single-step transition: advance along matching edges ---
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
    # If any state requires end-of-line, the match end must satisfy EOL or EOF
    n = len(text)
    for u in S:
        if states[u].require_eol:
            if "m" in flags:
                if not (pos_after == n or (pos_after < n and text[pos_after] == "\n")):
                    return False
            else:
                if pos_after != n:
                    return False
    return True


# ---------------------------------------------------------------------------
# Public: return only spans (legacy helper for engine unit tests)
# ---------------------------------------------------------------------------
def match(pattern: str, text: str, flags: str = "") -> list[tuple[int, int]]:
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    spans: list[tuple[int, int]] = []

    i = 0
    N = len(text)
    while i <= N:
        # Starting ε-closure (check anchors at position i)
        S = _eps_closure_at(nfa.states, {nfa.start}, i, text, flags)
        j = i
        best_j: int | None = None

        # Acceptable immediately (empty match / pure anchors)
        Sc = _eps_closure_at(nfa.states, S, j, text, flags)
        if any(nfa.states[s].accept for s in Sc) and _ok_eol(
            nfa.states, Sc, j, text, flags
        ):
            best_j = j

        # Consume characters to find the longest match for this start
        while j < N:
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

        if best_j is not None:
            spans.append((i, best_j))
            # Non-overlapping: advance at least 1 if zero-length
            i = best_j if best_j > i else i + 1
        else:
            i += 1

    return spans


# ---------------------------------------------------------------------------
# Public: return spans + groups (for API, closer to "re" style)
# ---------------------------------------------------------------------------
def match_with_groups(pattern: str, text: str, flags: str = "") -> list[dict]:
    tree = parser.parse(pattern)
    nfa = compile_nfa(tree)
    out: list[dict] = []

    i = 0
    N = len(text)
    while i <= N:
        S = _eps_closure_at(nfa.states, {nfa.start}, i, text, flags)
        j = i

        # Track the longest match (greedy) and its groups for this start
        best_j: int | None = None
        group_starts: dict[int, int] = {}
        group_spans: dict[int, tuple[int, int]] = {}
        best_groups: dict[int, tuple[int, int]] | None = None

        def apply_group_hooks(state_set: set[int], pos: int):
            # Record group start/end based on enter/exit hooks on states
            for s in state_set:
                st = nfa.states[s]
                for g in st.enter_groups:
                    group_starts[g] = pos
                for g in st.exit_groups:
                    st_pos = group_starts.get(g)
                    if st_pos is not None:
                        group_spans[g] = (st_pos, pos)

        # Apply hooks on initial closure
        Sc = _eps_closure_at(nfa.states, S, j, text, flags)
        apply_group_hooks(Sc, j)
        if any(nfa.states[s].accept for s in Sc) and _ok_eol(
            nfa.states, Sc, j, text, flags
        ):
            best_j = j
            best_groups = dict(group_spans)

        # Consume characters to find the longest match and capture groups
        while j < N:
            Sc = _eps_closure_at(nfa.states, S, j, text, flags)
            S = _step(nfa.states, Sc, text[j], flags)
            if not S:
                break
            j += 1
            Sc2 = _eps_closure_at(nfa.states, S, j, text, flags)
            apply_group_hooks(Sc2, j)
            if any(nfa.states[s].accept for s in Sc2) and _ok_eol(
                nfa.states, Sc2, j, text, flags
            ):
                best_j = j
                best_groups = dict(group_spans)

        if best_j is not None:
            # Normalize groups: fill 1..max_idx, use None for missing
            groups_norm: list[tuple[int, int] | None] = []
            if best_groups:
                max_idx = max(best_groups)
                groups_norm = [None] * max_idx
                for k, span in best_groups.items():
                    if k >= 1:
                        if k > len(groups_norm):
                            groups_norm.extend([None] * (k - len(groups_norm)))
                        groups_norm[k - 1] = span
            out.append({"span": (i, best_j), "groups": groups_norm})
            i = best_j if best_j > i else i + 1
        else:
            i += 1

    return out


def match_spans(pattern: str, text: str, flags: str = "") -> list[tuple[int, int]]:
    """Return only the match spans; thin wrapper over :func:`match`."""

    return match(pattern, text, flags)


def replace(pattern: str, flags: str, text: str, repl: str) -> Tuple[str, int]:
    """
    Replace all matches of pattern in text with repl string.
    Returns tuple of (result_text, count_of_replacements).
    Note: Does not support backreferences in replacement string yet.
    """
    spans = match_spans(pattern, text, flags)

    if not spans:
        # If no matches, return original text and zero replacements
        return text, 0

    # Build result by replacing matches from right to left
    # (avoids offset adjustments)
    result = text
    count = len(spans)

    for start, end in reversed(spans):
        result = result[:start] + repl + result[end:]

    return result, count


def split(pattern: str, text: str, flags: str = "") -> list[str]:
    """Split text by matches of pattern; return list of substrings between matches."""

    spans = match_spans(pattern, text, flags)

    if not spans:
        return [text]

    pieces: list[str] = []
    last_end = 0

    for start, end in spans:
        pieces.append(text[last_end:start])
        last_end = end

    pieces.append(text[last_end:])
    return pieces
