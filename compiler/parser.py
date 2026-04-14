"""
Recursive Descent Parser.

Converts a token stream into an Abstract Syntax Tree (AST).

Grammar (informal EBNF):
    program         = { function_decl }
    function_decl   = "int" IDENT "(" [param_list] ")" block
    param_list      = "int" IDENT { "," "int" IDENT }
    block           = "{" { statement } "}"
    statement       = var_decl
                    | if_stmt
                    | while_stmt
                    | return_stmt
                    | print_stmt
                    | assignment_or_expr_stmt
    var_decl        = "int" IDENT [ "=" expr ] ";"
    if_stmt         = "if" "(" expr ")" block [ "else" block ]
    while_stmt      = "while" "(" expr ")" block
    return_stmt     = "return" [ expr ] ";"
    print_stmt      = "print" "(" expr ")" ";"
    assignment_or_expr_stmt = IDENT "=" expr ";" | expr ";"

Expression precedence (lowest to highest):
    or_expr         = and_expr { "||" and_expr }
    and_expr        = equality { "&&" equality }
    equality        = comparison { ("==" | "!=") comparison }
    comparison      = addition { ("<" | ">" | "<=" | ">=") addition }
    addition        = multiplication { ("+" | "-") multiplication }
    multiplication  = unary { ("*" | "/" | "%") unary }
    unary           = ("-" | "!") unary | primary
    primary         = NUMBER | IDENT [ "(" [arg_list] ")" ] | "(" expr ")"
"""

from __future__ import annotations

from compiler.lexer import Token, TokenType, Lexer
from compiler.ast_nodes import (
    Program, FunctionDecl, Parameter, Block,
    VarDecl, IfStatement, WhileStatement, ReturnStatement,
    PrintStatement, ExpressionStatement, Assignment,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, FunctionCall,
    ASTNode,
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(
            f"Parse error at L{token.line}:{token.col}: {message} "
            f"(got {token.type.name} '{token.value}')"
        )


class Parser:
    """Recursive-descent parser for our C subset."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _at(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _consume(self, expected: TokenType, context: str = "") -> Token:
        tok = self._current()
        if tok.type != expected:
            msg = f"Expected {expected.name}"
            if context:
                msg += f" {context}"
            raise ParseError(msg, tok)
        self.pos += 1
        return tok

    def _match(self, *types: TokenType) -> Token | None:
        if self._current().type in types:
            tok = self._current()
            self.pos += 1
            return tok
        return None

    # ------------------------------------------------------------------
    # Top-level
    # ------------------------------------------------------------------

    def parse(self) -> Program:
        """Parse the full program."""
        functions: list[FunctionDecl] = []
        while not self._at(TokenType.EOF):
            functions.append(self._parse_function_decl())
        return Program(functions=functions, line=1, col=1)

    def _parse_function_decl(self) -> FunctionDecl:
        tok_int = self._consume(TokenType.INT, "at start of function declaration")
        name_tok = self._consume(TokenType.IDENTIFIER, "for function name")
        self._consume(TokenType.LPAREN, "after function name")

        params: list[Parameter] = []
        if not self._at(TokenType.RPAREN):
            params = self._parse_param_list()

        self._consume(TokenType.RPAREN, "after parameter list")
        body = self._parse_block()

        return FunctionDecl(
            name=name_tok.value, params=params, body=body,
            line=tok_int.line, col=tok_int.col,
        )

    def _parse_param_list(self) -> list[Parameter]:
        params: list[Parameter] = []
        self._consume(TokenType.INT, "for parameter type")
        name = self._consume(TokenType.IDENTIFIER, "for parameter name")
        params.append(Parameter(name=name.value, line=name.line, col=name.col))

        while self._match(TokenType.COMMA):
            self._consume(TokenType.INT, "for parameter type")
            name = self._consume(TokenType.IDENTIFIER, "for parameter name")
            params.append(Parameter(name=name.value, line=name.line, col=name.col))

        return params

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _parse_block(self) -> Block:
        tok = self._consume(TokenType.LBRACE, "at start of block")
        stmts: list[ASTNode] = []
        while not self._at(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._parse_statement())
        self._consume(TokenType.RBRACE, "at end of block")
        return Block(statements=stmts, line=tok.line, col=tok.col)

    def _parse_statement(self) -> ASTNode:
        cur = self._current()

        if cur.type == TokenType.INT:
            return self._parse_var_decl()
        if cur.type == TokenType.IF:
            return self._parse_if()
        if cur.type == TokenType.WHILE:
            return self._parse_while()
        if cur.type == TokenType.RETURN:
            return self._parse_return()
        if cur.type == TokenType.PRINT:
            return self._parse_print()
        if cur.type == TokenType.LBRACE:
            return self._parse_block()

        # Assignment or expression statement
        return self._parse_assignment_or_expr_stmt()

    def _parse_var_decl(self) -> VarDecl:
        tok = self._consume(TokenType.INT)
        name = self._consume(TokenType.IDENTIFIER, "for variable name")
        init = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expr()
        self._consume(TokenType.SEMICOLON, "after variable declaration")
        return VarDecl(name=name.value, init=init, line=tok.line, col=tok.col)

    def _parse_if(self) -> IfStatement:
        tok = self._consume(TokenType.IF)
        self._consume(TokenType.LPAREN, "after 'if'")
        cond = self._parse_expr()
        self._consume(TokenType.RPAREN, "after if condition")
        then_block = self._parse_block()
        else_block = None
        if self._match(TokenType.ELSE):
            else_block = self._parse_block()
        return IfStatement(
            condition=cond, then_block=then_block, else_block=else_block,
            line=tok.line, col=tok.col,
        )

    def _parse_while(self) -> WhileStatement:
        tok = self._consume(TokenType.WHILE)
        self._consume(TokenType.LPAREN, "after 'while'")
        cond = self._parse_expr()
        self._consume(TokenType.RPAREN, "after while condition")
        body = self._parse_block()
        return WhileStatement(
            condition=cond, body=body,
            line=tok.line, col=tok.col,
        )

    def _parse_return(self) -> ReturnStatement:
        tok = self._consume(TokenType.RETURN)
        value = None
        if not self._at(TokenType.SEMICOLON):
            value = self._parse_expr()
        self._consume(TokenType.SEMICOLON, "after return statement")
        return ReturnStatement(value=value, line=tok.line, col=tok.col)

    def _parse_print(self) -> PrintStatement:
        tok = self._consume(TokenType.PRINT)
        self._consume(TokenType.LPAREN, "after 'print'")
        value = self._parse_expr()
        self._consume(TokenType.RPAREN, "after print argument")
        self._consume(TokenType.SEMICOLON, "after print statement")
        return PrintStatement(value=value, line=tok.line, col=tok.col)

    def _parse_assignment_or_expr_stmt(self) -> ASTNode:
        cur = self._current()
        # Look ahead: IDENT "=" -> assignment
        if cur.type == TokenType.IDENTIFIER and self._peek().type == TokenType.ASSIGN:
            name_tok = self._consume(TokenType.IDENTIFIER)
            self._consume(TokenType.ASSIGN)
            value = self._parse_expr()
            self._consume(TokenType.SEMICOLON, "after assignment")
            return Assignment(
                name=name_tok.value, value=value,
                line=name_tok.line, col=name_tok.col,
            )

        expr = self._parse_expr()
        self._consume(TokenType.SEMICOLON, "after expression statement")
        return ExpressionStatement(expr=expr, line=cur.line, col=cur.col)

    # ------------------------------------------------------------------
    # Expressions (precedence climbing)
    # ------------------------------------------------------------------

    def _parse_expr(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._at(TokenType.OR):
            tok = self._consume(TokenType.OR)
            right = self._parse_and()
            left = BinaryOp(op="||", left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_equality()
        while self._at(TokenType.AND):
            tok = self._consume(TokenType.AND)
            right = self._parse_equality()
            left = BinaryOp(op="&&", left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_equality(self) -> ASTNode:
        left = self._parse_comparison()
        while self._at(TokenType.EQ, TokenType.NEQ):
            tok = self._current()
            self.pos += 1
            right = self._parse_comparison()
            left = BinaryOp(op=tok.value, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_addition()
        while self._at(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            tok = self._current()
            self.pos += 1
            right = self._parse_addition()
            left = BinaryOp(op=tok.value, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_addition(self) -> ASTNode:
        left = self._parse_multiplication()
        while self._at(TokenType.PLUS, TokenType.MINUS):
            tok = self._current()
            self.pos += 1
            right = self._parse_multiplication()
            left = BinaryOp(op=tok.value, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_multiplication(self) -> ASTNode:
        left = self._parse_unary()
        while self._at(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            tok = self._current()
            self.pos += 1
            right = self._parse_unary()
            left = BinaryOp(op=tok.value, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def _parse_unary(self) -> ASTNode:
        if self._at(TokenType.MINUS, TokenType.NOT):
            tok = self._current()
            self.pos += 1
            operand = self._parse_unary()
            return UnaryOp(op=tok.value, operand=operand, line=tok.line, col=tok.col)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        # Integer literal
        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLiteral(value=int(tok.value), line=tok.line, col=tok.col)

        # Identifier or function call
        if tok.type == TokenType.IDENTIFIER:
            self.pos += 1
            # Function call?
            if self._at(TokenType.LPAREN):
                self._consume(TokenType.LPAREN)
                args: list[ASTNode] = []
                if not self._at(TokenType.RPAREN):
                    args.append(self._parse_expr())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expr())
                self._consume(TokenType.RPAREN, "after function arguments")
                return FunctionCall(name=tok.value, args=args, line=tok.line, col=tok.col)
            return Identifier(name=tok.value, line=tok.line, col=tok.col)

        # Parenthesized expression
        if tok.type == TokenType.LPAREN:
            self._consume(TokenType.LPAREN)
            expr = self._parse_expr()
            self._consume(TokenType.RPAREN, "after parenthesized expression")
            return expr

        raise ParseError("Expected expression", tok)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def parse_source(source: str) -> Program:
    """Lex and parse source code in one call."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()
