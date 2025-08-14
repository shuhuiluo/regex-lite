from regex_lite import ast, parser


def test_alternation_precedence():
    tree = parser.parse("a|bc")
    assert isinstance(tree, ast.Alternation)
    assert isinstance(tree.right, ast.Sequence)


def test_grouping():
    tree = parser.parse("(ab)c")
    assert isinstance(tree, ast.Sequence)
    assert isinstance(tree.parts[0], ast.Group)
