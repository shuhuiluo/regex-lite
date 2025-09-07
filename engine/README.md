# Engine Checklist

* [ ] **Define subset & flags** (readme spec): literals, `. [] ^ $ () | * + ? {m,n}`, escapes, ranges; flags `i/m/s/g`;
  anchors `^/$`.
* [ ] **Tokens** (`tokens.py`): metachars, escapes (inside/outside `[]`), `\t \n \r \xHH`, shorthands as
  `Shorthand('d'|'w'|'s'|…)`.
* [ ] **Lexer** (`lexer.py`): one-pass with positions; class rules (negation if first `^`, ranges with `-`, literal `-`
  and `]` handling).
* [ ] **AST dataclasses** (`ast.py`):
  `Literal, Dot, AnchorStart, AnchorEnd, CharClass, Range, Group(index), Concat, Alt, Repeat, Shorthand`.
* [ ] **Parser** (`parser.py`): Pratt or shunting-yard; implicit concatenation; group numbering; quantifier validation (
  `{m}`, `{m,}`, `{m,n}` with `m≤n`); precise error types.
* [ ] **Thompson compiler** (`compiler.py`): per-node builders

    * [ ] `Literal`, `Dot` (respect `s` flag), `Shorthand` (defer to char sets)
    * [ ] `CharClass` (negated & ranges), `Concat`, `Alt`, `Repeat(* + ? {m,n})`
    * [ ] `Group` capture entry/exit hooks (indexing)
    * [ ] Anchors `^/$` as start/end constraints
* [ ] **Matcher** (`matcher.py`): ε-closure NFA simulation

    * [ ] Case-folding for `i`, line vs. string semantics for `m`, dotall for `s`
    * [ ] First vs. global (`g`) search; leftmost-longest greedy behavior
    * [ ] Capture spans for numbered groups
* [ ] **Replace / Split semantics**: `$1…` back-refs; count; split with `limit` (optional)
* [ ] **Performance sanity**: typical pattern compiles <150ms; match small texts <5–10ms; simple micro-bench script

# Testing

* [ ] **Unit (engine)**

    * [ ] Lexer: escapes, ranges, `[]` edge cases
    * [ ] Parser: precedence (`a|bc*`), grouping, quantifiers, anchors
    * [ ] Compiler/Matcher: literals/dot/classes/alt/concat/repeat, flags, anchors, captures
* [ ] **Property tests** (Hypothesis): random small patterns/inputs vs Python `re` where semantics overlap
* [ ] **Golden tests**: curated patterns → expected spans/captures; replace/split outputs
