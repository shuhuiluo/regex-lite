from __future__ import annotations

from .tokens import Token, TokenType


class Lexer:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        i = 0
        while i < len(self.pattern):
            ch = self.pattern[i]
            if ch == "\\":
                i += 1
                if i >= len(self.pattern):
                    raise ValueError("dangling escape")
                tokens.append(Token(TokenType.CHAR, self.pattern[i]))
            elif ch == ".":
                tokens.append(Token(TokenType.DOT))
            elif ch == "*":
                tokens.append(Token(TokenType.STAR))
            elif ch == "+":
                tokens.append(Token(TokenType.PLUS))
            elif ch == "?":
                tokens.append(Token(TokenType.QUESTION))
            elif ch == "(":
                tokens.append(Token(TokenType.LPAREN))
            elif ch == ")":
                tokens.append(Token(TokenType.RPAREN))
            elif ch == "|":
                tokens.append(Token(TokenType.PIPE))
            else:
                tokens.append(Token(TokenType.CHAR, ch))
            i += 1
        tokens.append(Token(TokenType.EOF))
        return tokens


def tokenize(pattern: str) -> list[Token]:
    return Lexer(pattern).tokenize()
