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


class NFA:
    """NFA (Non-deterministic Finite Automaton) compiled from regex AST."""

    def __init__(self, tree: ast.Node):
        self.states: List[State] = []
        self.start, _ = self._build(tree)

    # === Low-level state operations ===

    def _new_state(self, accept: bool = False) -> int:
        self.states.append(State(accept=accept))
        return len(self.states) - 1

    def _add_eps(self, u: int, v: int) -> None:
        self.states[u].eps.append(v)

    def _add_edge(self, u: int, kind: str, data: Any, v: int) -> None:
        self.states[u].edges.append(Edge(kind, data, v))

    def _mark_accept(self, i: int, val: bool) -> None:
        self.states[i].accept = val

    # === Fragment construction ===

    def _frag_literal(self, ch: str) -> Tuple[int, int]:
        s = self._new_state()
        a = self._new_state(True)
        self._add_edge(s, "char", ch, a)
        return s, a

    def _frag_dot(self) -> Tuple[int, int]:
        s = self._new_state()
        a = self._new_state(True)
        self._add_edge(s, "dot", None, a)
        return s, a

    def _frag_shorthand(self, kind: str) -> Tuple[int, int]:
        # kind in {'d','w','s'} — interpreted in matcher
        s = self._new_state()
        a = self._new_state(True)
        self._add_edge(s, "pred", kind, a)
        return s, a

    def _frag_charclass(self, negated: bool, items: Iterable) -> Tuple[int, int]:
        lits: Set[str] = set()
        ranges: List[Tuple[str, str]] = []
        for it in items:
            if isinstance(it, ast.Range):
                ranges.append((str(it.start), str(it.end)))
            elif isinstance(it, ast.Literal):
                lits.add(str(it.char))
            else:
                raise TypeError(
                    f"Unexpected character class item type {type(it).__name__}: {it!r}"
                )
        s = self._new_state()
        a = self._new_state(True)
        self._add_edge(s, "class", (negated, frozenset(lits), tuple(ranges)), a)
        return s, a

    def _frag_concat(self, frags: List[Tuple[int, int]]) -> Tuple[int, int]:
        if not frags:
            # Empty string
            s = self._new_state()
            a = self._new_state(True)
            self._add_eps(s, a)
            return s, a
        s0, a0 = frags[0]
        for s1, a1 in frags[1:]:
            self._mark_accept(a0, False)
            self._add_eps(a0, s1)
            a0 = a1
        self._mark_accept(a0, True)
        return s0, a0

    def _frag_alt(
        self, left: Tuple[int, int], right: Tuple[int, int]
    ) -> Tuple[int, int]:
        s = self._new_state()
        a = self._new_state(True)
        ls, la = left
        rs, ra = right
        self._mark_accept(la, False)
        self._mark_accept(ra, False)
        self._add_eps(s, ls)
        self._add_eps(s, rs)
        self._add_eps(la, a)
        self._add_eps(ra, a)
        return s, a

    def _clone_fragment(self, base: Tuple[int, int]) -> Tuple[int, int]:
        """
        Creates a fresh copy of a fragment by cloning all states reachable from base.
        Returns a new (start, accept) pair with completely new state indices.
        """
        start_old, accept_old = base

        # Map old state indices to new state indices
        state_map = {}

        # Collect all reachable states from the fragment via DFS
        reachable = set()
        stack = [start_old]
        while stack:
            state_idx = stack.pop()
            if state_idx in reachable:
                continue
            reachable.add(state_idx)

            state = self.states[state_idx]
            # Add epsilon transitions
            for eps_target in state.eps:
                if eps_target not in reachable:
                    stack.append(eps_target)
            # Add edge transitions
            for edge in state.edges:
                if edge.to not in reachable:
                    stack.append(edge.to)

        # Create new states for all reachable states
        for old_idx in reachable:
            old_state = self.states[old_idx]
            new_idx = self._new_state(old_state.accept)
            state_map[old_idx] = new_idx

            # Copy other state properties
            new_state = self.states[new_idx]
            new_state.require_bol = old_state.require_bol
            new_state.require_eol = old_state.require_eol
            new_state.enter_groups = old_state.enter_groups.copy()
            new_state.exit_groups = old_state.exit_groups.copy()

        # Clone all edges and epsilon transitions
        for old_idx in reachable:
            old_state = self.states[old_idx]
            new_idx = state_map[old_idx]
            new_state = self.states[new_idx]

            # Clone epsilon transitions
            for eps_target in old_state.eps:
                if eps_target in state_map:
                    new_state.eps.append(state_map[eps_target])

            # Clone edges
            for edge in old_state.edges:
                if edge.to in state_map:
                    new_state.edges.append(
                        Edge(edge.kind, edge.data, state_map[edge.to])
                    )

        return state_map[start_old], state_map[accept_old]

    def _repeat_range(
        self, base: Tuple[int, int], min_: int, max_: Optional[int]
    ) -> Tuple[int, int]:
        """
        Thompson expansion: repeat at least `min_` times + optionally (max_-min_) times;
        max_=None means no upper limit.
        """
        if max_ is not None and max_ < min_:
            raise ValueError(f"Invalid repeat range: {{{min_},{max_}}} (max < min)")
        # Start with an empty entry state
        s_all = self._new_state()
        cur_a = s_all  # initially empty
        # Required min_ repetitions: concatenate sequentially
        for _ in range(min_):
            s, a = self._clone_fragment(base)
            self._mark_accept(a, False)
            self._add_eps(cur_a, s)
            cur_a = a

        if min_ == 0:
            # Allow empty: jump from start directly to current a
            cur_a = s_all

        # Finite upper bound: add (max_-min_) optional repetitions
        if max_ is not None:
            reps = max(0, max_ - min_)
            for _ in range(reps):
                s, a = self._clone_fragment(base)
                self._mark_accept(a, False)

                # Create new accept for this optional iteration
                new_a = self._new_state()

                # Option: skip to new_a
                self._add_eps(cur_a, new_a)
                # Or: take base once
                self._add_eps(cur_a, s)
                self._add_eps(a, new_a)

                cur_a = new_a

            # End
            self._mark_accept(cur_a, True)
            return s_all, cur_a

        # No upper bound: add loop at the tail
        s, a = self._clone_fragment(base)
        self._mark_accept(a, False)

        loop_state = self._new_state()

        # From current position to loop entry
        self._add_eps(cur_a, loop_state)

        # From loop: either exit (will mark true later) or take base once more
        self._add_eps(loop_state, s)
        self._add_eps(a, loop_state)

        self._mark_accept(loop_state, True)
        return s_all, loop_state

    # === AST traversal ===

    def _build(self, node: ast.Node) -> Tuple[int, int]:
        # Literal
        if isinstance(node, ast.Literal):
            return self._frag_literal(node.char)

        # Dot
        if isinstance(node, ast.Dot):
            return self._frag_dot()

        # Shorthands: \d \w \s
        if isinstance(node, ast.Shorthand):
            return self._frag_shorthand(node.kind)

        # Character class
        if isinstance(node, ast.CharClass):
            return self._frag_charclass(node.negated, node.items)

        # Concatenation
        if isinstance(node, ast.Concat):
            parts = [self._build(p) for p in node.parts]
            return self._frag_concat(parts)

        # Alternation (multi-branch Alt.options)
        if isinstance(node, ast.Alt):
            assert node.options, "Alt.options should be non-empty"
            fr = self._build(node.options[0])
            for opt in node.options[1:]:
                fr = self._frag_alt(fr, self._build(opt))
            return fr

        # Quantifiers: node.kind is '*', '+', '?', or like '{m}', '{m,}', '{m,n}'
        if isinstance(node, ast.Repeat):
            inner = self._build(node.expr)

            k = node.kind
            if k == "*":
                return self._repeat_range(inner, 0, None)
            if k == "+":
                return self._repeat_range(inner, 1, None)
            if k == "?":
                return self._repeat_range(inner, 0, 1)

            # Template with m/n fields
            if k in ("{m}", "{m,}", "{m,n}"):
                m = node.m if node.m is not None else 0
                n = node.n  # None means no upper bound
                return self._repeat_range(inner, m, n)

            # Fallback: parse literal "{2,3}" kind string
            if k.startswith("{") and k.endswith("}"):
                body = k[1:-1]
                if "," not in body:
                    m = int(body)
                    return self._repeat_range(inner, m, m)
                left, right = body.split(",", 1)
                m = int(left) if left.strip() else 0
                n = None if right.strip() == "" else int(right)
                return self._repeat_range(inner, m, n)

            raise ValueError(f"unknown repeat kind: {k}")

        # Group
        if isinstance(node, ast.Group):
            s, a = self._build(node.expr)
            self.states[s].enter_groups.append(node.index)
            self.states[a].exit_groups.append(node.index)
            return s, a

        # Anchors
        if isinstance(node, ast.AnchorStart):
            s = self._new_state()
            a = self._new_state(True)
            self.states[s].require_bol = True
            self._add_eps(s, a)
            return s, a

        if isinstance(node, ast.AnchorEnd):
            s = self._new_state()
            a = self._new_state(True)
            self.states[s].require_eol = True
            self._add_eps(s, a)
            return s, a

        # Allow empty (if Empty node exists)
        if hasattr(ast, "Empty") and isinstance(node, ast.Empty):
            s = self._new_state()
            a = self._new_state(True)
            self._add_eps(s, a)
            return s, a

        raise NotImplementedError(f"compile: unsupported node {type(node).__name__}")


def compile(tree: ast.Node) -> NFA:
    return NFA(tree)
