from __future__ import annotations

from typing import List

from . import ast
from .lexer import tokenize
from .tokens import Token, TokenType


class RegexSyntaxError(Exception):
    """Raised when the pattern contains a syntax error."""

    def __init__(self, message: str, position: int | None = None) -> None:
        if position is not None:
            message = f"{message} at position {position}"
        super().__init__(message)
        self.position = position


class Parser:
    """Pratt parser turning token stream into an AST."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.group_index = 0

    # ----------------------------------------------------------- utilities
    def peek(self, k: int = 0) -> Token:
        return self.tokens[self.pos + k]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def match(self, typ: TokenType) -> bool:
        if self.peek().type == typ:
            self.advance()
            return True
        return False

    def expect(self, typ: TokenType, msg: str) -> Token:
        if self.peek().type != typ:
            raise RegexSyntaxError(msg, self.peek().pos)
        return self.advance()

    # ----------------------------------------------------------- entry point
    def parse(self) -> ast.Expr:
        """Parse the token stream and return the root AST node."""

        expr = self.parse_alt()
        self.expect(TokenType.EOF, "unexpected trailing characters")
        return expr

    # ----------------------------------------------------------- grammar
    def parse_alt(self) -> ast.Expr:
        """Parse alternation ``a|b|c`` (lowest precedence)."""

        left = self.parse_concat()
        options = [left]
        while self.match(TokenType.PIPE):
            options.append(self.parse_concat())
        if len(options) == 1:
            return left
        return ast.Alt(options)

    def parse_concat(self) -> ast.Expr:
        """Parse an implicit concatenation ``AB`` of one or more expressions."""

        parts: List[ast.Expr] = []
        while True:
            t = self.peek()
            if t.type in {TokenType.EOF, TokenType.RPAREN, TokenType.PIPE}:
                break
            # handle stray '?' after a quantifier (e.g. '+?') as a literal
            if (
                t.type == TokenType.QUESTION
                and parts
                and isinstance(parts[-1], ast.Repeat)
            ):
                self.advance()
                parts.append(ast.Literal("?"))
                continue
            parts.append(self.parse_repeat())
        if not parts:
            raise RegexSyntaxError("expected expression", self.peek().pos)
        if len(parts) == 1:
            return parts[0]
        return ast.Concat(parts)

    def parse_repeat(self) -> ast.Expr:
        """Parse postfix quantifiers like ``*`` or ``{m,n}``."""

        if self.peek().type in {
            TokenType.STAR,
            TokenType.PLUS,
            TokenType.QUESTION,
            TokenType.LBRACE,
        }:
            raise RegexSyntaxError("quantifier without target", self.peek().pos)
        expr = self.parse_primary()
        applied = False
        while True:
            t = self.peek()
            if t.type == TokenType.QUESTION and applied:
                break
            if t.type == TokenType.STAR:
                self.advance()
                expr = ast.Repeat(expr, "*")
                applied = True
            elif t.type == TokenType.PLUS:
                self.advance()
                expr = ast.Repeat(expr, "+")
                applied = True
            elif t.type == TokenType.QUESTION:
                self.advance()
                expr = ast.Repeat(expr, "?")
                applied = True
            elif t.type == TokenType.LBRACE:
                expr = self._parse_brace_quant(expr)
                applied = True
            else:
                break
        return expr

    def _parse_number(self) -> int | None:
        """Read a decimal number from the input, returning ``None`` if absent."""

        digits: List[str] = []
        while self.peek().type == TokenType.CHAR and self.peek().value.isdigit():
            digits.append(self.advance().value)
        if not digits:
            return None
        return int("".join(digits))

    def _parse_brace_quant(self, expr: ast.Expr) -> ast.Expr:
        """Parse a ``{m}``, ``{m,}`` or ``{m,n}`` quantifier."""

        lbrace = self.advance()  # consume '{'
        start_pos = lbrace.pos
        m = self._parse_number()
        if m is None:
            raise RegexSyntaxError("expected number", self.peek().pos)
        if self.match(TokenType.RBRACE):
            return ast.Repeat(expr, "{m}", m, m)
        self.expect(TokenType.COMMA, "expected ',' in quantifier")
        if self.match(TokenType.RBRACE):
            return ast.Repeat(expr, "{m,}", m, None)
        n = self._parse_number()
        if n is None:
            raise RegexSyntaxError("expected number", self.peek().pos)
        if m > n:
            raise RegexSyntaxError("invalid range in quantifier", start_pos)
        self.expect(TokenType.RBRACE, "expected '}'")
        return ast.Repeat(expr, "{m,n}", m, n)

    def parse_primary(self) -> ast.Expr:
        """Parse an atomic expression such as a literal, group, or class."""

        t = self.peek()
        if t.type == TokenType.CHAR:
            self.advance()
            return ast.Literal(t.value)
        if t.type == TokenType.DOT:
            self.advance()
            return ast.Dot()
        if t.type == TokenType.CARET:
            self.advance()
            return ast.AnchorStart()
        if t.type == TokenType.DOLLAR:
            self.advance()
            return ast.AnchorEnd()
        if t.type == TokenType.SHORTHAND:
            self.advance()
            return ast.Shorthand(t.value)
        if t.type == TokenType.LPAREN:
            self.advance()
            self.group_index += 1
            idx = self.group_index
            expr = self.parse_alt()
            self.expect(TokenType.RPAREN, "unmatched '('")
            return ast.Group(expr, idx)
        if t.type == TokenType.LBRACKET:
            return self.parse_char_class()
        raise RegexSyntaxError("unexpected token", t.pos)

    def parse_char_class(self) -> ast.CharClass:
        """Parse a character class, including ranges and negation."""

        self.expect(TokenType.LBRACKET, "expected '['")
        negated = False
        if self.peek().type == TokenType.CARET:
            self.advance()
            negated = True
        items: List[ast.ClassItem] = []
        while True:
            t = self.peek()
            if t.type == TokenType.RBRACKET:
                self.advance()
                break
            item = self._parse_class_atom()
            if (
                self.peek().type == TokenType.DASH
                and self.peek(1).type != TokenType.RBRACKET
            ):
                self.advance()  # consume '-'
                end = self._parse_class_atom()
                if not isinstance(item, ast.Literal) or not isinstance(
                    end, ast.Literal
                ):
                    raise RegexSyntaxError("invalid range", t.pos)
                if ord(item.char) > ord(end.char):
                    raise RegexSyntaxError("invalid range", t.pos)
                items.append(ast.Range(item.char, end.char))
            else:
                items.append(item)
        return ast.CharClass(items, negated)

    def _parse_class_atom(self) -> ast.ClassItem:
        """Parse a single item within a character class."""

        t = self.peek()
        if t.type == TokenType.EOF:
            raise RegexSyntaxError("unterminated character class", t.pos)
        if t.type == TokenType.CHAR:
            self.advance()
            return ast.Literal(t.value)
        if t.type == TokenType.SHORTHAND:
            self.advance()
            return ast.Shorthand(t.value)
        if t.type == TokenType.DASH:
            self.advance()
            return ast.Literal("-")
        if t.type == TokenType.CARET:
            self.advance()
            return ast.Literal("^")
        # Any other token inside class is treated as literal of its value
        self.advance()
        return ast.Literal(t.value if t.value is not None else "")


def parse(pattern: str) -> ast.Expr:
    """Parse ``pattern`` into an :class:`ast.Expr` tree."""

    tokens = tokenize(pattern)
    parser = Parser(tokens)
    return parser.parse()
