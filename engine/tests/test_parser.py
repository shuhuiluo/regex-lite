import pytest
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from regex_lite import ast, parser


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


def test_quantifiers_and_literals():
    tree = parser.parse("a{2,3}b+?")
    assert isinstance(tree, ast.Concat)
    a_rep, b_rep, q = tree.parts
    assert (
        isinstance(a_rep, ast.Repeat)
        and a_rep.kind == "{m,n}"
        and a_rep.m == 2
        and a_rep.n == 3
    )
    assert isinstance(b_rep, ast.Repeat) and b_rep.kind == "+"
    assert isinstance(q, ast.Literal) and q.char == "?"


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


def test_errors():
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("(a")  # unmatched )
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("{,3}")
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("{3,2}")
    with pytest.raises(parser.RegexSyntaxError):
        parser.parse("*a")
