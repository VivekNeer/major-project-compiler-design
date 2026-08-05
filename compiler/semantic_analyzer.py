"""
Semantic Analyzer.

Validates the AST between parsing and IR generation. The parser only
enforces syntax; this phase enforces the language rules that syntax
cannot express:

  - every variable is declared before use
  - no duplicate declaration within one scope
  - called functions exist and are called with the right argument count
  - no duplicate function definitions
  - arrays are indexed and scalars are not
  - array names are not used as bare values
  - a main() function exists
  - global initialisers are compile-time constants

All violations in a program are collected and reported together, so a
user sees every error in one compile instead of fixing them one at a
time.
"""

from __future__ import annotations
from dataclasses import dataclass

from compiler.ast_nodes import (
    Program, FunctionDecl, Block,
    VarDecl, ArrayDecl, IfStatement, WhileStatement, ForStatement,
    ReturnStatement,
    PrintStatement, ExpressionStatement, Assignment, ArrayAssignment,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, FunctionCall, ArrayAccess,
    ASTNode,
)
from compiler.errors import CompilerError


class SemanticError(CompilerError):
    """Raised when a program violates semantic rules.

    Carries the full list of issues; the message joins them all.
    """

    def __init__(self, issues: list["SemanticIssue"]):
        self.issues = issues
        # Expose the first issue's location for error reporters
        self.line = issues[0].line if issues else 0
        self.col = issues[0].col if issues else 0
        super().__init__("; ".join(str(i) for i in issues))


@dataclass
class SemanticIssue:
    """A single semantic violation with source location."""
    message: str
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return f"L{self.line}:{self.col}: {self.message}"


class SemanticAnalyzer:
    """AST-walking semantic checker with its own scope stack."""

    def __init__(self) -> None:
        self._issues: list[SemanticIssue] = []
        # Scope stack: each scope maps name -> "int" | "array" | "global"
        self._scopes: list[dict[str, str]] = []
        # Function name -> parameter count
        self._functions: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def analyze(self, program: Program) -> list[SemanticIssue]:
        """Check the whole program and return all issues found."""
        self._issues = []
        self._scopes = [{}]

        # Collect function signatures first so calls can appear before
        # definitions in source order.
        self._functions = {}
        for func in program.functions:
            if func.name in self._functions:
                self._error(f"Function '{func.name}' is defined more than once",
                            func)
            else:
                self._functions[func.name] = len(func.params)

        if "main" not in self._functions:
            self._issues.append(SemanticIssue("No main() function defined"))

        for glob in program.globals:
            if glob.name in self._functions:
                self._error(
                    f"Global '{glob.name}' conflicts with a function of the same name",
                    glob,
                )
            self._check_global(glob)
        for func in program.functions:
            self._check_function(func)

        return self._issues

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _error(self, message: str, node: ASTNode) -> None:
        self._issues.append(SemanticIssue(message, node.line, node.col))

    def _declare(self, name: str, kind: str, node: ASTNode) -> None:
        current = self._scopes[-1]
        if name in current:
            self._error(f"Variable '{name}' already declared in this scope", node)
        else:
            current[name] = kind

    def _lookup(self, name: str) -> str | None:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def _is_const_expr(self, node: ASTNode) -> bool:
        if isinstance(node, NumberLiteral):
            return True
        if isinstance(node, UnaryOp) and node.op == "-":
            return self._is_const_expr(node.operand)
        return False

    # ------------------------------------------------------------------
    # Declarations
    # ------------------------------------------------------------------

    def _check_global(self, node: VarDecl) -> None:
        if node.init is not None and not self._is_const_expr(node.init):
            self._error(
                f"Global '{node.name}' initializer must be a constant expression",
                node,
            )
        self._declare(node.name, "global", node)

    def _check_function(self, func: FunctionDecl) -> None:
        self._scopes.append({})
        for param in func.params:
            self._declare(param.name, "int", param)
        self._check_block(func.body)
        self._scopes.pop()

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _check_block(self, block: Block) -> None:
        self._scopes.append({})
        for stmt in block.statements:
            self._check_statement(stmt)
        self._scopes.pop()

    def _check_statement(self, node: ASTNode) -> None:
        if isinstance(node, VarDecl):
            if node.init is not None:
                self._check_expr(node.init)
            self._declare(node.name, "int", node)
        elif isinstance(node, ArrayDecl):
            self._declare(node.name, "array", node)
        elif isinstance(node, Assignment):
            self._check_assignment_target(node.name, node)
            self._check_expr(node.value)
        elif isinstance(node, ArrayAssignment):
            kind = self._lookup(node.name)
            if kind is None:
                self._error(f"Undeclared variable '{node.name}'", node)
            elif kind != "array":
                self._error(f"'{node.name}' is not an array", node)
            self._check_expr(node.index)
            self._check_expr(node.value)
        elif isinstance(node, IfStatement):
            self._check_expr(node.condition)
            self._check_block(node.then_block)
            if node.else_block is not None:
                self._check_block(node.else_block)
        elif isinstance(node, WhileStatement):
            self._check_expr(node.condition)
            self._check_block(node.body)
        elif isinstance(node, ForStatement):
            self._scopes.append({})
            if node.init is not None:
                self._check_statement(node.init)
            if node.condition is not None:
                self._check_expr(node.condition)
            self._check_block(node.body)
            if node.update is not None:
                self._check_statement(node.update)
            self._scopes.pop()
        elif isinstance(node, ReturnStatement):
            if node.value is not None:
                self._check_expr(node.value)
        elif isinstance(node, PrintStatement):
            self._check_expr(node.value)
        elif isinstance(node, ExpressionStatement):
            self._check_expr(node.expr)
        elif isinstance(node, Block):
            self._check_block(node)

    def _check_assignment_target(self, name: str, node: ASTNode) -> None:
        kind = self._lookup(name)
        if kind is None:
            self._error(f"Undeclared variable '{name}'", node)
        elif kind == "array":
            self._error(f"Cannot assign to array '{name}' without an index", node)

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _check_expr(self, node: ASTNode) -> None:
        if isinstance(node, NumberLiteral):
            return
        if isinstance(node, Identifier):
            kind = self._lookup(node.name)
            if kind is None:
                self._error(f"Undeclared variable '{node.name}'", node)
            elif kind == "array":
                self._error(
                    f"Array '{node.name}' cannot be used as a value without an index",
                    node,
                )
            return
        if isinstance(node, ArrayAccess):
            kind = self._lookup(node.name)
            if kind is None:
                self._error(f"Undeclared variable '{node.name}'", node)
            elif kind != "array":
                self._error(f"'{node.name}' is not an array", node)
            self._check_expr(node.index)
            return
        if isinstance(node, BinaryOp):
            self._check_expr(node.left)
            self._check_expr(node.right)
            return
        if isinstance(node, UnaryOp):
            self._check_expr(node.operand)
            return
        if isinstance(node, FunctionCall):
            if node.name not in self._functions:
                self._error(f"Call to undefined function '{node.name}'", node)
            else:
                expected = self._functions[node.name]
                if len(node.args) != expected:
                    self._error(
                        f"Function '{node.name}' expects {expected} "
                        f"argument{'s' if expected != 1 else ''}, "
                        f"got {len(node.args)}",
                        node,
                    )
            for arg in node.args:
                self._check_expr(arg)
            return
        if isinstance(node, Assignment):
            self._check_assignment_target(node.name, node)
            self._check_expr(node.value)
            return


def check_semantics(program: Program) -> None:
    """Analyze the program and raise SemanticError if any issue exists."""
    issues = SemanticAnalyzer().analyze(program)
    if issues:
        raise SemanticError(issues)
