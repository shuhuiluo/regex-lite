# regex_lite/compiler.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Set, Tuple

from . import ast  # Adapt to your current ast.py (relative import within the package)

# ---------- NFA structure ----------


@dataclass
class Edge:
    # kind: 'char' | 'dot' | 'pred' | 'class'
    kind: str
    data: Any
    to: int


@dataclass
class State:
    edges: List[Edge] = field(default_factory=list)
    eps: List[int] = field(default_factory=list)
    accept: bool = False
    # Anchor constraints (checked in matcher)
    require_bol: bool = False
    require_eol: bool = False
    # Group enter/exit hooks (can be used in matcher if capture is needed)
    enter_groups: List[int] = field(default_factory=list)
    exit_groups: List[int] = field(default_factory=list)


@dataclass
class NFA:
    states: List[State]
    start: int
    accepts: Set[int]


def _new_state(states: List[State], accept: bool = False) -> int:
    states.append(State(accept=accept))
    return len(states) - 1


def _add_eps(states: List[State], u: int, v: int) -> None:
    states[u].eps.append(v)


def _add_edge(states: List[State], u: int, kind: str, data: Any, v: int) -> None:
    states[u].edges.append(Edge(kind, data, v))


def _mark_accept(states: List[State], i: int, val: bool) -> None:
    states[i].accept = val


# ---------- Fragment construction: return (start, accept) ----------


def _frag_literal(states: List[State], ch: str) -> Tuple[int, int]:
    s = _new_state(states)
    a = _new_state(states, True)
    _add_edge(states, s, "char", ch, a)
    return s, a


def _frag_dot(states: List[State]) -> Tuple[int, int]:
    s = _new_state(states)
    a = _new_state(states, True)
    _add_edge(states, s, "dot", None, a)
    return s, a


def _frag_shorthand(states: List[State], kind: str) -> Tuple[int, int]:
    # kind in {'d','w','s'} — interpreted in matcher
    s = _new_state(states)
    a = _new_state(states, True)
    _add_edge(states, s, "pred", kind, a)
    return s, a


def _frag_charclass(
    states: List[State], negated: bool, items: Iterable
) -> Tuple[int, int]:
    from . import ast as A

    lits: Set[str] = set()
    ranges: List[Tuple[str, str]] = []
    for it in items:
        if isinstance(it, A.Range):
            ranges.append((str(it.start), str(it.end)))
        elif isinstance(it, A.Literal):
            lits.add(str(it.char))
        else:
            # Fallback: treat as a character
            lits.add(str(it))
    s = _new_state(states)
    a = _new_state(states, True)
    _add_edge(states, s, "class", (negated, frozenset(lits), tuple(ranges)), a)
    return s, a


def _frag_concat(states: List[State], frags: List[Tuple[int, int]]) -> Tuple[int, int]:
    if not frags:
        # Empty string
        s = _new_state(states)
        a = _new_state(states, True)
        _add_eps(states, s, a)
        return s, a
    s0, a0 = frags[0]
    for s1, a1 in frags[1:]:
        _mark_accept(states, a0, False)
        _add_eps(states, a0, s1)
        a0 = a1
    _mark_accept(states, a0, True)
    return s0, a0


def _frag_alt(
    states: List[State], left: Tuple[int, int], right: Tuple[int, int]
) -> Tuple[int, int]:
    s = _new_state(states)
    a = _new_state(states, True)
    ls, la = left
    rs, ra = right
    _mark_accept(states, la, False)
    _mark_accept(states, ra, False)
    _add_eps(states, s, ls)
    _add_eps(states, s, rs)
    _add_eps(states, la, a)
    _add_eps(states, ra, a)
    return s, a


def _repeat_range(
    states: List[State], base: Tuple[int, int], min_: int, max_: Optional[int]
) -> Tuple[int, int]:
    """
    Thompson expansion: repeat at least `min_` times + optionally (max_-min_) times;
    max_=None means no upper limit.
    """
    # First build an "empty fragment" (for concatenation convenience)
    s_all = _new_state(states)
    a_all = _new_state(states, True)
    _mark_accept(states, a_all, False)  # will be reset later

    _cur_s, cur_a = s_all, s_all  # initially empty
    # Required min_ repetitions: concatenate sequentially
    for _ in range(min_):
        s, a = base
        midS = _new_state(states)
        midA = _new_state(states, True)
        _mark_accept(states, midA, False)

        if cur_a == s_all:
            # Initial connection
            _add_eps(states, s_all, midS)
        else:
            _add_eps(states, cur_a, midS)

        _add_eps(states, midS, s)
        _add_eps(states, a, midA)
        cur_a = midA

    if min_ == 0:
        # Allow empty: jump from start directly to current a
        cur_a = s_all

    # Finite upper bound: add (max_-min_) optional repetitions
    if max_ is not None:
        reps = max(0, max_ - min_)
        for _ in range(reps):
            s, a = base
            midS = _new_state(states)
            midA = _new_state(states, True)
            _mark_accept(states, midA, False)

            # Option: skip to midA
            _add_eps(states, cur_a, midA)
            # Or: take base once
            _add_eps(states, cur_a, midS)
            _add_eps(states, midS, s)
            _add_eps(states, a, midA)

            cur_a = midA

        # End
        _mark_accept(states, cur_a, True)
        return s_all, cur_a

    # No upper bound: add loop at the tail
    s, a = base
    loopS = _new_state(states)
    loopA = _new_state(states, True)
    _mark_accept(states, loopA, False)

    if cur_a == s_all:
        _add_eps(states, s_all, loopS)
    else:
        _add_eps(states, cur_a, loopS)

    # Optionally skip
    _add_eps(states, loopS, loopA)
    # Or execute base once and go to loopA
    _add_eps(states, loopS, s)
    _add_eps(states, a, loopA)
    # From loopA back to loopS for repetition
    _add_eps(states, loopA, loopS)

    _mark_accept(states, loopA, True)
    return s_all, loopA


# ---------- AST traversal ----------


def _build(node: ast.Node, states: List[State]) -> Tuple[int, int]:
    # Literal
    if isinstance(node, ast.Literal):
        return _frag_literal(states, node.char)

    # Dot
    if isinstance(node, ast.Dot):
        return _frag_dot(states)

    # Shorthands: \d \w \s
    if isinstance(node, ast.Shorthand):
        return _frag_shorthand(states, node.kind)

    # Character class
    if isinstance(node, ast.CharClass):
        return _frag_charclass(states, node.negated, node.items)

    # Concatenation
    if isinstance(node, ast.Concat):
        parts = [_build(p, states) for p in node.parts]
        return _frag_concat(states, parts)

    # Alternation (multi-branch Alt.options)
    if isinstance(node, ast.Alt):
        assert node.options, "Alt.options should be non-empty"
        fr = _build(node.options[0], states)
        for opt in node.options[1:]:
            fr = _frag_alt(states, fr, _build(opt, states))
        return fr

    # Quantifiers: node.kind is '*', '+', '?', or like '{m}', '{m,}', '{m,n}'
    if isinstance(node, ast.Repeat):
        inner = _build(node.expr, states)

        k = node.kind
        if k == "*":
            return _repeat_range(states, inner, 0, None)
        if k == "+":
            return _repeat_range(states, inner, 1, None)
        if k == "?":
            return _repeat_range(states, inner, 0, 1)

        # Template with m/n fields
        if k in ("{m}", "{m,}", "{m,n}"):
            m = node.m if node.m is not None else 0
            n = node.n  # None means no upper bound
            return _repeat_range(states, inner, m, n)

        # Fallback: parse literal "{2,3}" kind string
        if k.startswith("{") and k.endswith("}"):
            body = k[1:-1]
            if "," not in body:
                m = int(body)
                return _repeat_range(states, inner, m, m)
            left, right = body.split(",", 1)
            m = int(left) if left.strip() else 0
            n = None if right.strip() == "" else int(right)
            return _repeat_range(states, inner, m, n)

        raise ValueError(f"unknown repeat kind: {k}")

    # Group
    if isinstance(node, ast.Group):
        s, a = _build(node.expr, states)
        states[s].enter_groups.append(node.index)
        states[a].exit_groups.append(node.index)
        return s, a

    # Anchors
    if isinstance(node, ast.AnchorStart):
        s = _new_state(states)
        a = _new_state(states, True)
        states[s].require_bol = True
        _add_eps(states, s, a)
        return s, a

    if isinstance(node, ast.AnchorEnd):
        s = _new_state(states)
        a = _new_state(states, True)
        states[s].require_eol = True
        _add_eps(states, s, a)
        return s, a

    # Allow empty (if Empty node exists)
    if hasattr(ast, "Empty") and isinstance(node, ast.Empty):
        s = _new_state(states)
        a = _new_state(states, True)
        _add_eps(states, s, a)
        return s, a

    raise NotImplementedError(f"compile: unsupported node {type(node).__name__}")


def compile(tree: ast.Node) -> NFA:
    states: List[State] = []
    start, _ = _build(tree, states)
    accepts = {i for i, st in enumerate(states) if st.accept}
    return NFA(states=states, start=start, accepts=accepts)
