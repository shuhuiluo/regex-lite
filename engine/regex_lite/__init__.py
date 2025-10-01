"""regex_lite engine package."""

from .lexer import Lexer, tokenize
from .matcher import match_spans, match_with_groups, replace, split
from .parser import RegexSyntaxError

__all__ = [
    "Lexer",
    "tokenize",
    "match_spans",
    "match_with_groups",
    "replace",
    "split",
    "RegexSyntaxError",
]
