"""
Lexical Analyzer (Lexer / Tokenizer).

Converts raw source text into a stream of tokens. Handles:
  - Keywords: int, if, else, while, return, print
  - Identifiers and integer literals
  - Operators: arithmetic, comparison, logical, assignment
  - Delimiters: parentheses, braces, semicolons, commas
  - Single-line (//) and multi-line (/* */) comments
  - Whitespace skipping with line/column tracking
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator


class TokenType(Enum):
    # Literals & identifiers
    NUMBER = auto()
    IDENTIFIER = auto()

    # Keywords
    INT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()

    # Arithmetic operators
    PLUS = auto()       # +
    MINUS = auto()      # -
    STAR = auto()       # *
    SLASH = auto()      # /
    PERCENT = auto()    # %

    # Comparison operators
    EQ = auto()         # ==
    NEQ = auto()        # !=
    LT = auto()         # <
    GT = auto()         # >
    LTE = auto()        # <=
    GTE = auto()        # >=

    # Logical operators
    AND = auto()        # &&
    OR = auto()         # ||
    NOT = auto()        # !

    # Assignment
    ASSIGN = auto()     # =

    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    SEMICOLON = auto()  # ;
    COMMA = auto()      # ,

    # Special
    EOF = auto()


KEYWORDS = {
    "int": TokenType.INT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        self.line = line
        self.col = col
        super().__init__(f"Lexer error at L{line}:{col}: {message}")


class Lexer:
    """Tokenizes source code into a stream of Token objects."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current(self) -> str:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return "\0"

    def _peek(self, offset: int = 1) -> str:
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return "\0"

    def _advance(self) -> str:
        ch = self._current()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self) -> None:
        while self.pos < len(self.source) and self._current() in " \t\n\r":
            self._advance()

    def _skip_line_comment(self) -> None:
        while self.pos < len(self.source) and self._current() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        start_line, start_col = self.line, self.col
        self._advance()  # skip *
        while self.pos < len(self.source):
            if self._current() == "*" and self._peek() == "/":
                self._advance()  # skip *
                self._advance()  # skip /
                return
            self._advance()
        raise LexerError("Unterminated block comment", start_line, start_col)

    def _skip_whitespace_and_comments(self) -> None:
        while self.pos < len(self.source):
            if self._current() in " \t\n\r":
                self._skip_whitespace()
            elif self._current() == "/" and self._peek() == "/":
                self._skip_line_comment()
            elif self._current() == "/" and self._peek() == "*":
                self._advance()  # skip /
                self._skip_block_comment()
            else:
                break

    # ------------------------------------------------------------------
    # Token readers
    # ------------------------------------------------------------------

    def _read_number(self) -> Token:
        start_col = self.col
        digits = []
        while self.pos < len(self.source) and self._current().isdigit():
            digits.append(self._advance())
        # Guard against identifiers starting with digits
        if self.pos < len(self.source) and (self._current().isalpha() or self._current() == "_"):
            raise LexerError(
                f"Invalid number literal '{''.join(digits)}{self._current()}'",
                self.line, start_col,
            )
        return Token(TokenType.NUMBER, "".join(digits), self.line, start_col)

    def _read_identifier_or_keyword(self) -> Token:
        start_col = self.col
        chars = []
        while self.pos < len(self.source) and (self._current().isalnum() or self._current() == "_"):
            chars.append(self._advance())
        word = "".join(chars)
        tt = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(tt, word, self.line, start_col)

    # ------------------------------------------------------------------
    # Main interface
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        """Return the full list of tokens (including EOF)."""
        return list(self._generate_tokens())

    def _generate_tokens(self) -> Iterator[Token]:
        """Yield tokens one at a time."""
        while True:
            self._skip_whitespace_and_comments()

            if self.pos >= len(self.source):
                yield Token(TokenType.EOF, "", self.line, self.col)
                return

            line, col = self.line, self.col
            ch = self._current()

            # --- Numbers ---
            if ch.isdigit():
                yield self._read_number()
                continue

            # --- Identifiers / keywords ---
            if ch.isalpha() or ch == "_":
                yield self._read_identifier_or_keyword()
                continue

            # --- Two-character operators ---
            two = ch + self._peek()
            if two == "==":
                self._advance(); self._advance()
                yield Token(TokenType.EQ, "==", line, col); continue
            if two == "!=":
                self._advance(); self._advance()
                yield Token(TokenType.NEQ, "!=", line, col); continue
            if two == "<=":
                self._advance(); self._advance()
                yield Token(TokenType.LTE, "<=", line, col); continue
            if two == ">=":
                self._advance(); self._advance()
                yield Token(TokenType.GTE, ">=", line, col); continue
            if two == "&&":
                self._advance(); self._advance()
                yield Token(TokenType.AND, "&&", line, col); continue
            if two == "||":
                self._advance(); self._advance()
                yield Token(TokenType.OR, "||", line, col); continue

            # --- Single-character operators / delimiters ---
            single_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "!": TokenType.NOT,
                "=": TokenType.ASSIGN,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ";": TokenType.SEMICOLON,
                ",": TokenType.COMMA,
            }

            if ch in single_map:
                self._advance()
                yield Token(single_map[ch], ch, line, col)
                continue

            raise LexerError(f"Unexpected character '{ch}'", line, col)
