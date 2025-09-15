import pytest
from regex_lite import ast, parser


def test_empty_pattern():
    tree = parser.parse("")
    assert isinstance(tree, ast.Empty)


def test_literal_and_concat():
    assert isinstance(parser.parse("a"), ast.Literal)
    tree = parser.parse("ab")
    assert isinstance(tree, ast.Concat)
    assert [p.char for p in tree.parts] == ["a", "b"]


def test_simple_alternation():
    tree = parser.parse("a|b")
    assert isinstance(tree, ast.Alt)
    assert all(isinstance(opt, ast.Literal) for opt in tree.options)


def test_empty_group():
    tree = parser.parse("()")
    assert isinstance(tree, ast.Group)
    assert isinstance(tree.expr, ast.Empty)
    assert tree.index == 1


def test_precedence():
    tree = parser.parse("a|bc*")
    assert isinstance(tree, ast.Alt)
    assert isinstance(tree.options[0], ast.Literal)
    assert tree.options[0].char == "a"
    assert isinstance(tree.options[1], ast.Concat)
    b, repeat = tree.options[1].parts
    assert isinstance(b, ast.Literal) and b.char == "b"
    assert isinstance(repeat, ast.Repeat)
    assert repeat.kind == "*"
    assert isinstance(repeat.expr, ast.Literal) and repeat.expr.char == "c"


def test_grouping():
    tree = parser.parse("(ab|c)d")
    assert isinstance(tree, ast.Concat)
    group, d = tree.parts
    assert isinstance(group, ast.Group)
    assert group.index == 1
    assert isinstance(group.expr, ast.Alt)
    assert isinstance(d, ast.Literal) and d.char == "d"


def test_nested_group_numbering():
    tree = parser.parse("(a(b)c)")
    assert isinstance(tree, ast.Group) and tree.index == 1
    assert isinstance(tree.expr, ast.Concat)
    a, inner, c = tree.expr.parts
    assert isinstance(a, ast.Literal) and a.char == "a"
    assert isinstance(inner, ast.Group) and inner.index == 2
    assert isinstance(inner.expr, ast.Literal) and inner.expr.char == "b"
    assert isinstance(c, ast.Literal) and c.char == "c"


def test_quantifiers_and_literals():
    tree = parser.parse("a{2,3}b+c?")
    assert isinstance(tree, ast.Concat)
    a_rep, b_rep, c_rep = tree.parts
    assert (
        isinstance(a_rep, ast.Repeat)
        and a_rep.kind == "{m,n}"
        and a_rep.m == 2
        and a_rep.n == 3
    )
    assert isinstance(b_rep, ast.Repeat) and b_rep.kind == "+"
    assert isinstance(c_rep, ast.Repeat) and c_rep.kind == "?"


def test_lazy_quantifiers():
    tree = parser.parse("a*?b+?c??d{2,3}?")
    assert isinstance(tree, ast.Concat)
    a_rep, b_rep, c_rep, d_rep = tree.parts
    assert isinstance(a_rep, ast.Repeat) and a_rep.kind == "*" and a_rep.lazy
    assert isinstance(b_rep, ast.Repeat) and b_rep.kind == "+" and b_rep.lazy
    assert isinstance(c_rep, ast.Repeat) and c_rep.kind == "?" and c_rep.lazy
    assert (
        isinstance(d_rep, ast.Repeat)
        and d_rep.kind == "{m,n}"
        and d_rep.m == 2
        and d_rep.n == 3
        and d_rep.lazy
    )


def test_char_class_and_anchors():
    tree = parser.parse("[^a-z\\-]")
    assert isinstance(tree, ast.CharClass)
    assert tree.negated is True
    assert len(tree.items) == 2
    rng, dash = tree.items
    assert isinstance(rng, ast.Range) and rng.start == "a" and rng.end == "z"
    assert isinstance(dash, ast.Literal) and dash.char == "-"

    tree = parser.parse("^\\d+$")
    assert isinstance(tree, ast.Concat)
    assert isinstance(tree.parts[0], ast.AnchorStart)
    assert isinstance(tree.parts[1], ast.Repeat)
    assert isinstance(tree.parts[1].expr, ast.Shorthand)
    assert isinstance(tree.parts[-1], ast.AnchorEnd)


def test_char_class_punctuation_literals():
    tree = parser.parse("[.*+?(){}|]")
    assert isinstance(tree, ast.CharClass)
    assert [item.char for item in tree.items] == list(".*+?(){}|")


def test_char_class_errors():
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("[z-a]")
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("[abc")


def test_errors():
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("(a")  # unmatched )
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("{,3}")
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("{3,2}")
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("*a")
