# Engine Checklist

* [x] **Define subset & flags** (readme spec): literals, `. [] ^ $ () | * + ? {m,n}`, escapes, ranges; flags `i/m/s`;
  anchors `^/$`.
* [x] **Tokens** (`tokens.py`): metachars, escapes (inside/outside `[]`), `\t \n \r \xHH`, shorthands as
  `Shorthand('d'|'w'|'s'|…)`.
* [x] **Lexer** (`lexer.py`): one-pass with positions; class rules (negation if first `^`, ranges with `-`, literal `-`
  and `]` handling).
* [x] **AST dataclasses** (`ast.py`):
  `Literal, Dot, AnchorStart, AnchorEnd, CharClass, Range, Group(index), Concat, Alt, Repeat, Shorthand`.
* [x] **Parser** (`parser.py`): Pratt or shunting-yard; implicit concatenation; group numbering; quantifier validation (
  `{m}`, `{m,}`, `{m,n}` with `m≤n`); precise error types.
* [x] **Thompson compiler** (`compiler.py`): per-node builders

    * [x] `Literal`, `Dot` (respect `s` flag), `Shorthand` (defer to char sets)
    * [x] `CharClass` (negated & ranges), `Concat`, `Alt`, `Repeat(* + ? {m,n})`
    * [x] `Group` capture entry/exit hooks (indexing)
    * [x] Anchors `^/$` as start/end constraints
* [x] **Matcher** (`matcher.py`): ε-closure NFA simulation

    * [x] Case-folding for `i`, line vs. string semantics for `m`, dotall for `s`
    * [x] Leftmost-longest greedy behavior (global search by default)
    * [x] Capture spans for numbered groups
* [ ] **Replace / Split semantics**: `$1…` back-refs; count; split with `limit` (optional)
* [x] **Performance sanity**: typical pattern compiles <150ms; match small texts <5–10ms; simple micro-bench script

# Testing

* [x] **Unit (engine)**

    * [x] Lexer: escapes, ranges, `[]` edge cases
    * [x] Parser: precedence (`a|bc*`), grouping, quantifiers, anchors
    * [x] Compiler/Matcher: literals/dot/classes/alt/concat/repeat, flags, anchors, captures
* [x] **Property tests** (Hypothesis): random small patterns/inputs vs Python `re` where semantics overlap
* [x] **Golden tests**: curated patterns → expected spans/captures; replace/split outputs


# Supported Syntax

| **Feature**            | **Syntax**     | **Description**                                                           | **Example**         | **Matches** |          |
| ---------------------- | -------------- | ------------------------------------------------------------------------- | ------------------- | ----------- | -------- |
| **Literal characters** | `abc`          | Matches characters literally                                              | `abc` on `xxabcxx`  | `abc`       |          |
| **Any character**      | `.`            | Matches any character except newline (or including newline with `s` flag) | `a.c` on `axc`      | `axc`       |          |
| **Character classes**  | `[abc]`        | Matches one character from the set                                        | `[abc]` on `xay`    | `a`         |          |
| **Character ranges**   | `[a-z]`        | Matches one character from the range                                      | `[a-c]` on `zab`    | `a`, `b`    |          |
| **Negated classes**    | `[^abc]`       | Matches one character *not* in the set                                    | `[^a]` on `bat`     | `b`, `t`    |          |
| **Anchors**            | `^` / `$`      | Match start / end of string (or line with `m` flag)                       | `^ab` on `abxx`     | `ab`        |          |
| **Grouping**           | `( ... )`      | Groups sub-expressions (capturing supported)                              | `(ab)+` on `ababx`  | `abab`      |          |
| **Alternation**        | `a\|b`         | Matches left or right branch                                              | \`a                 | b`on`bab\`  | `b`, `b` |
| **Quantifiers**        | `* + ? {m,n}`  | Repetition: 0+ / 1+ / 0-1 / range                                         | `a{2,3}` on `caaad` | `aaa`       |          |
| **Escapes**            | `\d \w \s`     | Shorthand classes (digit/word/space)                                      | `\d+` on `ab123c`   | `123`       |          |
| **Escaped literals**   | `\.` `\+` etc. | Treat metacharacter as literal                                            | `a\.b` on `a.b`     | `a.b`       |          |

# Supported Flags

| **Flag** | **Name**    | **Effect**                                                        |
| -------- | ----------- | ----------------------------------------------------------------- |
| `i`      | Ignore Case | Case-insensitive matching (`A` = `a`)                             |
| `m`      | Multiline   | `^` and `$` match at line boundaries                              |
| `s`      | Dotall      | `.` matches `\n` as well                                          |

Note: Global search (returning all matches) is the default behavior of this engine.
