"""
Abstract Syntax Tree (AST) node definitions.

Each node represents a syntactic construct in our C subset language.
Uses dataclasses for clean, immutable representations with source
location tracking for error reporting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class ASTNode:
    """Base class for all AST nodes. Carries source location."""
    line: int = 0
    col: int = 0


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass
class NumberLiteral(ASTNode):
    """Integer literal, e.g. 42"""
    value: int = 0


@dataclass
class Identifier(ASTNode):
    """Variable reference, e.g. x"""
    name: str = ""


@dataclass
class BinaryOp(ASTNode):
    """Binary operation, e.g. a + b, x < y, p && q"""
    op: str = ""
    left: ASTNode = field(default_factory=ASTNode)
    right: ASTNode = field(default_factory=ASTNode)


@dataclass
class UnaryOp(ASTNode):
    """Unary operation, e.g. -x, !flag"""
    op: str = ""
    operand: ASTNode = field(default_factory=ASTNode)


@dataclass
class FunctionCall(ASTNode):
    """Function call expression, e.g. foo(a, b)"""
    name: str = ""
    args: list[ASTNode] = field(default_factory=list)


@dataclass
class Assignment(ASTNode):
    """Assignment expression, e.g. x = expr (also used as statement)"""
    name: str = ""
    value: ASTNode = field(default_factory=ASTNode)


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class VarDecl(ASTNode):
    """Variable declaration: int x; or int x = expr;"""
    name: str = ""
    init: Optional[ASTNode] = None


@dataclass
class ExpressionStatement(ASTNode):
    """Statement consisting of a single expression (e.g. function call)."""
    expr: ASTNode = field(default_factory=ASTNode)


@dataclass
class Block(ASTNode):
    """Brace-enclosed block of statements: { ... }"""
    statements: list[ASTNode] = field(default_factory=list)


@dataclass
class IfStatement(ASTNode):
    """if (cond) then_block [else else_block]"""
    condition: ASTNode = field(default_factory=ASTNode)
    then_block: Block = field(default_factory=Block)
    else_block: Optional[Block] = None


@dataclass
class WhileStatement(ASTNode):
    """while (cond) body"""
    condition: ASTNode = field(default_factory=ASTNode)
    body: Block = field(default_factory=Block)


@dataclass
class ReturnStatement(ASTNode):
    """return expr;"""
    value: Optional[ASTNode] = None


@dataclass
class PrintStatement(ASTNode):
    """print(expr); — built-in output"""
    value: ASTNode = field(default_factory=ASTNode)


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

@dataclass
class Parameter(ASTNode):
    """Function parameter: int name"""
    name: str = ""


@dataclass
class FunctionDecl(ASTNode):
    """Function declaration: int name(params) { body }"""
    name: str = ""
    params: list[Parameter] = field(default_factory=list)
    body: Block = field(default_factory=Block)


@dataclass
class Program(ASTNode):
    """Root node — a program is a list of function declarations."""
    functions: list[FunctionDecl] = field(default_factory=list)
