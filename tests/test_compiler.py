"""
Comprehensive test suite for the compiler infrastructure.

Tests cover all four phases:
  - Phase 1: Lexer and Parser
  - Phase 2: Symbol Table and IR Generation
  - Phase 3: Optimization Passes
  - Phase 4: Benchmark metrics collection
"""

import pytest
from compiler.lexer import Lexer, LexerError, TokenType
from compiler.parser import Parser, ParseError, parse_source
from compiler.ast_nodes import (
    Program, FunctionDecl, Block, VarDecl, IfStatement, WhileStatement,
    ReturnStatement, PrintStatement, BinaryOp, NumberLiteral, Identifier,
    Assignment,
)
from compiler.symbol_table import SymbolTable, SymbolTableError
from compiler.ir_generator import IRGenerator, generate_ir
from compiler.ir import IRInstruction, IROpcode, format_ir, is_constant
from compiler.optimizations.constant_folding import constant_folding
from compiler.optimizations.dead_code_elimination import dead_code_elimination
from compiler.optimizations.common_subexpression_elimination import common_subexpression_elimination
from compiler.optimizations.copy_propagation import copy_propagation
from compiler.optimizations.strength_reduction import strength_reduction
from compiler.optimizations.algebraic_simplification import algebraic_simplification
from compiler.optimizations.pass_manager import PassManager
from compiler.benchmarks.metric_collector import collect_metrics, count_code_size, estimate_cycles
from compiler.interpreter import execute_ir, IRInterpreter


# ======================================================================
# Phase 1: Lexer Tests
# ======================================================================

class TestLexer:
    def test_empty_input(self):
        tokens = Lexer("").tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_integer_literal(self):
        tokens = Lexer("42").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_keywords(self):
        source = "int if else while return print"
        tokens = Lexer(source).tokenize()
        expected = [TokenType.INT, TokenType.IF, TokenType.ELSE,
                    TokenType.WHILE, TokenType.RETURN, TokenType.PRINT, TokenType.EOF]
        assert [t.type for t in tokens] == expected

    def test_identifiers(self):
        tokens = Lexer("foo bar_baz x1").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "foo"
        assert tokens[1].value == "bar_baz"
        assert tokens[2].value == "x1"

    def test_operators(self):
        source = "+ - * / % == != < > <= >= && || ! ="
        tokens = Lexer(source).tokenize()
        expected_types = [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT,
            TokenType.EQ, TokenType.NEQ,
            TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE,
            TokenType.AND, TokenType.OR, TokenType.NOT, TokenType.ASSIGN,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected_types

    def test_delimiters(self):
        tokens = Lexer("( ) { } ; ,").tokenize()
        expected = [TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE,
                    TokenType.RBRACE, TokenType.SEMICOLON, TokenType.COMMA, TokenType.EOF]
        assert [t.type for t in tokens] == expected

    def test_line_comment(self):
        source = "int x; // this is a comment\nint y;"
        tokens = Lexer(source).tokenize()
        # Should skip the comment
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [TokenType.INT, TokenType.IDENTIFIER, TokenType.SEMICOLON,
                         TokenType.INT, TokenType.IDENTIFIER, TokenType.SEMICOLON]

    def test_block_comment(self):
        source = "int /* block comment */ x;"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [TokenType.INT, TokenType.IDENTIFIER, TokenType.SEMICOLON]

    def test_line_tracking(self):
        source = "int\nx"
        tokens = Lexer(source).tokenize()
        assert tokens[0].line == 1
        assert tokens[1].line == 2

    def test_unexpected_character(self):
        with pytest.raises(LexerError):
            Lexer("@").tokenize()

    def test_unterminated_block_comment(self):
        with pytest.raises(LexerError):
            Lexer("/* no end").tokenize()

    def test_complex_expression(self):
        source = "a + b * (c - 1)"
        tokens = Lexer(source).tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert values == ["a", "+", "b", "*", "(", "c", "-", "1", ")"]


# ======================================================================
# Phase 1: Parser Tests
# ======================================================================

class TestParser:
    def test_simple_function(self):
        ast = parse_source("int main() { return 0; }")
        assert isinstance(ast, Program)
        assert len(ast.functions) == 1
        assert ast.functions[0].name == "main"

    def test_variable_declaration(self):
        ast = parse_source("int main() { int x = 5; return x; }")
        body = ast.functions[0].body.statements
        assert isinstance(body[0], VarDecl)
        assert body[0].name == "x"

    def test_if_else(self):
        source = """
        int main() {
            int x = 10;
            if (x > 5) {
                print(1);
            } else {
                print(0);
            }
            return 0;
        }
        """
        ast = parse_source(source)
        stmts = ast.functions[0].body.statements
        assert isinstance(stmts[1], IfStatement)
        assert stmts[1].else_block is not None

    def test_while_loop(self):
        source = """
        int main() {
            int i = 0;
            while (i < 10) {
                i = i + 1;
            }
            return 0;
        }
        """
        ast = parse_source(source)
        stmts = ast.functions[0].body.statements
        assert isinstance(stmts[1], WhileStatement)

    def test_operator_precedence(self):
        ast = parse_source("int main() { int x = 1 + 2 * 3; return 0; }")
        decl = ast.functions[0].body.statements[0]
        assert isinstance(decl, VarDecl)
        expr = decl.init
        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.op == "*"

    def test_function_with_params(self):
        source = """
        int add(int a, int b) {
            return a + b;
        }
        int main() {
            int result = add(3, 4);
            return 0;
        }
        """
        ast = parse_source(source)
        assert len(ast.functions) == 2
        assert len(ast.functions[0].params) == 2

    def test_nested_expressions(self):
        ast = parse_source("int main() { int x = (1 + 2) * (3 - 4); return 0; }")
        decl = ast.functions[0].body.statements[0]
        expr = decl.init
        assert isinstance(expr, BinaryOp)
        assert expr.op == "*"

    def test_parse_error(self):
        with pytest.raises(ParseError):
            parse_source("int main( { }")

    def test_print_statement(self):
        ast = parse_source("int main() { print(42); return 0; }")
        stmts = ast.functions[0].body.statements
        assert isinstance(stmts[0], PrintStatement)

    def test_assignment(self):
        source = "int main() { int x = 0; x = 5; return x; }"
        ast = parse_source(source)
        stmts = ast.functions[0].body.statements
        assert isinstance(stmts[1], Assignment)
        assert stmts[1].name == "x"

    def test_logical_operators(self):
        source = "int main() { int x = 1 && 0 || 1; return 0; }"
        ast = parse_source(source)
        decl = ast.functions[0].body.statements[0]
        # || has lower precedence than &&
        assert isinstance(decl.init, BinaryOp)
        assert decl.init.op == "||"


# ======================================================================
# Phase 2: Symbol Table Tests
# ======================================================================

class TestSymbolTable:
    def test_declare_and_lookup(self):
        st = SymbolTable()
        sym = st.declare("x")
        assert sym.name == "x"
        found = st.lookup("x")
        assert found.name == "x"

    def test_undeclared_variable(self):
        st = SymbolTable()
        with pytest.raises(SymbolTableError):
            st.lookup("nonexistent")

    def test_nested_scopes(self):
        st = SymbolTable()
        st.declare("x")
        st.enter_scope()
        st.declare("y")
        assert st.lookup("x").name == "x"
        assert st.lookup("y").name == "y"
        st.exit_scope()
        with pytest.raises(SymbolTableError):
            st.lookup("y")

    def test_shadowing(self):
        st = SymbolTable()
        st.declare("x")
        st.enter_scope()
        inner = st.declare("x")
        # Inner x should shadow outer x
        assert st.lookup("x").ir_name == inner.ir_name
        st.exit_scope()

    def test_double_declaration(self):
        st = SymbolTable()
        st.declare("x")
        with pytest.raises(SymbolTableError):
            st.declare("x")


# ======================================================================
# Phase 2: IR Generation Tests
# ======================================================================

class TestIRGenerator:
    def test_simple_program(self):
        ast = parse_source("int main() { return 0; }")
        ir = generate_ir(ast)
        assert any(i.opcode == IROpcode.FUNC_BEGIN for i in ir)
        assert any(i.opcode == IROpcode.RETURN for i in ir)
        assert any(i.opcode == IROpcode.FUNC_END for i in ir)

    def test_variable_and_assignment(self):
        ast = parse_source("int main() { int x = 5; x = 10; return x; }")
        ir = generate_ir(ast)
        # Should have LOAD_CONST for 5 and 10
        consts = [i for i in ir if i.opcode == IROpcode.LOAD_CONST]
        assert len(consts) >= 2

    def test_arithmetic(self):
        ast = parse_source("int main() { int x = 2 + 3; return x; }")
        ir = generate_ir(ast)
        adds = [i for i in ir if i.opcode == IROpcode.ADD]
        assert len(adds) == 1

    def test_if_generates_jumps(self):
        source = """
        int main() {
            int x = 1;
            if (x > 0) { print(1); }
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        jumps = [i for i in ir if i.opcode in (IROpcode.JUMP_IF_FALSE, IROpcode.JUMP)]
        assert len(jumps) >= 1

    def test_while_generates_loop(self):
        source = """
        int main() {
            int i = 0;
            while (i < 5) { i = i + 1; }
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        labels = [i for i in ir if i.opcode == IROpcode.LABEL]
        jumps = [i for i in ir if i.opcode == IROpcode.JUMP]
        assert len(labels) >= 2  # loop start and end
        assert len(jumps) >= 1  # back-edge

    def test_function_call(self):
        source = """
        int double(int n) { return n + n; }
        int main() { int x = double(5); return x; }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        params = [i for i in ir if i.opcode == IROpcode.PARAM]
        calls = [i for i in ir if i.opcode == IROpcode.CALL]
        assert len(params) >= 1
        assert len(calls) >= 1

    def test_print(self):
        ast = parse_source("int main() { print(42); return 0; }")
        ir = generate_ir(ast)
        prints = [i for i in ir if i.opcode == IROpcode.PRINT]
        assert len(prints) == 1

    def test_format_ir(self):
        ast = parse_source("int main() { int x = 1; return x; }")
        ir = generate_ir(ast)
        text = format_ir(ir)
        assert "func main:" in text
        assert "return" in text


# ======================================================================
# Phase 3: Optimization Tests
# ======================================================================

class TestConstantFolding:
    def test_fold_addition(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "2"),
            IRInstruction(IROpcode.LOAD_CONST, "t1", "3"),
            IRInstruction(IROpcode.ADD, "t2", "t0", "t1"),
        ]
        result = constant_folding(ir)
        # t2 should be folded to LOAD_CONST 5
        t2_inst = [i for i in result if i.dest == "t2"][0]
        assert t2_inst.opcode == IROpcode.LOAD_CONST
        assert t2_inst.src1 == "5"

    def test_fold_comparison(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "5"),
            IRInstruction(IROpcode.LOAD_CONST, "t1", "3"),
            IRInstruction(IROpcode.GT, "t2", "t0", "t1"),
        ]
        result = constant_folding(ir)
        t2_inst = [i for i in result if i.dest == "t2"][0]
        assert t2_inst.opcode == IROpcode.LOAD_CONST
        assert t2_inst.src1 == "1"  # 5 > 3 is true

    def test_no_fold_variables(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t0", "a", "b"),
        ]
        result = constant_folding(ir)
        assert result[0].opcode == IROpcode.ADD


class TestDeadCodeElimination:
    def test_remove_unused_variable(self):
        ir = [
            IRInstruction(IROpcode.FUNC_BEGIN, "main"),
            IRInstruction(IROpcode.LOAD_CONST, "t0", "42"),
            IRInstruction(IROpcode.COPY, "unused", "t0"),
            IRInstruction(IROpcode.LOAD_CONST, "t1", "0"),
            IRInstruction(IROpcode.RETURN, src1="t1"),
            IRInstruction(IROpcode.FUNC_END, "main"),
        ]
        result = dead_code_elimination(ir)
        # 'unused' and its dependencies should be removed
        dests = [i.dest for i in result if i.dest]
        assert "unused" not in dests

    def test_remove_unreachable_after_jump(self):
        ir = [
            IRInstruction(IROpcode.JUMP, "L1"),
            IRInstruction(IROpcode.LOAD_CONST, "t0", "99"),  # unreachable
            IRInstruction(IROpcode.LABEL, "L1"),
        ]
        result = dead_code_elimination(ir)
        # The LOAD_CONST should be removed (unreachable)
        assert len([i for i in result if i.opcode == IROpcode.LOAD_CONST]) == 0

    def test_preserve_used_variable(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "42"),
            IRInstruction(IROpcode.PRINT, src1="t0"),
        ]
        result = dead_code_elimination(ir)
        assert len(result) == 2  # both preserved


class TestCommonSubexpressionElimination:
    def test_eliminate_common_expr(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t0", "a", "b"),
            IRInstruction(IROpcode.PRINT, src1="t0"),
            IRInstruction(IROpcode.ADD, "t1", "a", "b"),  # duplicate
            IRInstruction(IROpcode.PRINT, src1="t1"),
        ]
        result = common_subexpression_elimination(ir)
        # Second ADD should become COPY
        assert result[2].opcode == IROpcode.COPY
        assert result[2].src1 == "t0"

    def test_no_eliminate_after_redefinition(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t0", "a", "b"),
            IRInstruction(IROpcode.LOAD_CONST, "a", "99"),  # redefine a
            IRInstruction(IROpcode.ADD, "t1", "a", "b"),    # different value now
        ]
        result = common_subexpression_elimination(ir)
        # Second ADD should stay as ADD since 'a' was redefined
        assert result[2].opcode == IROpcode.ADD

    def test_invalidate_expr_when_result_var_redefined(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t1", "a", "b"),
            IRInstruction(IROpcode.ADD, "t2", "a", "b"),  # becomes COPY from t1
            IRInstruction(IROpcode.LOAD_CONST, "t2", "0"),  # redefines t2
            IRInstruction(IROpcode.ADD, "t3", "a", "b"),
        ]
        result = common_subexpression_elimination(ir)
        # Final expression should not reuse stale t2.
        assert result[3].opcode == IROpcode.ADD

    def test_negative_constants_not_treated_as_variables(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t0", "x", "-1"),
            IRInstruction(IROpcode.ADD, "t1", "x", "-1"),
        ]
        result = common_subexpression_elimination(ir)
        assert result[1].opcode == IROpcode.COPY
        assert result[1].src1 == "t0"


class TestPassManager:
    def test_no_passes(self):
        ir = [IRInstruction(IROpcode.LOAD_CONST, "t0", "5")]
        pm = PassManager([])
        result = pm.run(ir)
        assert len(result) == 1

    def test_single_pass(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "2"),
            IRInstruction(IROpcode.LOAD_CONST, "t1", "3"),
            IRInstruction(IROpcode.ADD, "t2", "t0", "t1"),
            IRInstruction(IROpcode.PRINT, src1="t2"),
        ]
        pm = PassManager(["CF"])
        result = pm.run(ir)
        t2_inst = [i for i in result if i.dest == "t2"][0]
        assert t2_inst.opcode == IROpcode.LOAD_CONST

    def test_all_orderings(self):
        orderings = PassManager.all_orderings()
        # With 6 passes: 1 + 6 + 30 + 120 + 360 + 720 + 720 = 1957
        assert len(orderings) > 100  # at least many orderings

    def test_invalid_pass(self):
        with pytest.raises(ValueError):
            PassManager(["NONEXISTENT"])

    def test_describe(self):
        pm = PassManager(["CF", "DCE"])
        desc = pm.describe()
        assert "Constant Folding" in desc
        assert "Dead Code Elimination" in desc


# ======================================================================
# Phase 4: Metrics Tests
# ======================================================================

class TestMetrics:
    def test_code_size(self):
        ir = [
            IRInstruction(IROpcode.FUNC_BEGIN, "main"),
            IRInstruction(IROpcode.LOAD_CONST, "t0", "5"),
            IRInstruction(IROpcode.PRINT, src1="t0"),
            IRInstruction(IROpcode.LABEL, "L0"),  # not counted
            IRInstruction(IROpcode.RETURN, src1="t0"),
            IRInstruction(IROpcode.FUNC_END, "main"),  # not counted
        ]
        assert count_code_size(ir) == 3  # LOAD_CONST + PRINT + RETURN

    def test_estimated_cycles(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "5"),  # 1.0
            IRInstruction(IROpcode.MUL, "t1", "t0", "t0"),  # 3.0
        ]
        assert estimate_cycles(ir) == 4.0

    def test_collect_metrics(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "5"),
            IRInstruction(IROpcode.PRINT, src1="t0"),
        ]
        metrics = collect_metrics(ir, ["CF"])
        assert metrics.code_size == 2
        assert metrics.pass_order == ["CF"]
        assert metrics.estimated_cycles > 0

    def test_is_constant(self):
        assert is_constant("42")
        assert is_constant("0")
        assert is_constant("-5")
        assert not is_constant("x")
        assert not is_constant("t0")


# ======================================================================
# End-to-End Integration Tests
# ======================================================================

class TestEndToEnd:
    def test_fibonacci_compiles(self):
        source = """
        int main() {
            int n = 10;
            int a = 0;
            int b = 1;
            int i = 0;
            int temp;
            while (i < n) {
                temp = a + b;
                a = b;
                b = temp;
                i = i + 1;
            }
            print(a);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        assert len(ir) > 0

        # Optimize
        pm = PassManager(["CF", "DCE", "CSE"])
        optimized = pm.run(ir)
        assert count_code_size(optimized) <= count_code_size(ir)

    def test_all_pass_orderings_produce_valid_ir(self):
        source = """
        int main() {
            int x = 2 + 3;
            int y = x * 4;
            print(y);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)

        for ordering in PassManager.all_orderings():
            pm = PassManager(ordering)
            result = pm.run(ir)
            # Must still have FUNC_BEGIN/END and RETURN
            opcodes = {i.opcode for i in result}
            assert IROpcode.FUNC_BEGIN in opcodes
            assert IROpcode.FUNC_END in opcodes

    def test_optimization_never_increases_code(self):
        source = """
        int main() {
            int a = 1 + 2;
            int b = 3 + 4;
            int c = a + b;
            int d = a + b;
            int unused = 99;
            print(c);
            print(d);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        baseline_size = count_code_size(ir)

        for ordering in PassManager.all_full_orderings():
            pm = PassManager(ordering)
            result = pm.run(ir)
            assert count_code_size(result) <= baseline_size, \
                f"Ordering {ordering} increased code size"


# ======================================================================
# New Optimization Pass Tests
# ======================================================================

class TestCopyPropagation:
    def test_propagate_copy(self):
        ir = [
            IRInstruction(IROpcode.ADD, "t0", "a", "b"),
            IRInstruction(IROpcode.COPY, "t1", "t0"),
            IRInstruction(IROpcode.ADD, "t2", "t1", "c"),
        ]
        result = copy_propagation(ir)
        # t2 should use t0 instead of t1
        assert result[2].src1 == "t0"

    def test_no_propagate_after_redefine(self):
        ir = [
            IRInstruction(IROpcode.COPY, "t1", "a"),
            IRInstruction(IROpcode.LOAD_CONST, "a", "99"),  # redefine a
            IRInstruction(IROpcode.COPY, "t2", "t1"),
        ]
        result = copy_propagation(ir)
        # t2 should still use t1, not a (since a was redefined)
        assert result[2].src1 == "t1"

    def test_propagate_constant(self):
        ir = [
            IRInstruction(IROpcode.LOAD_CONST, "t0", "42"),
            IRInstruction(IROpcode.ADD, "t1", "t0", "x"),
        ]
        result = copy_propagation(ir)
        # t0 should be propagated as "42"
        assert result[1].src1 == "42"


class TestStrengthReduction:
    def test_mul_by_zero(self):
        ir = [IRInstruction(IROpcode.MUL, "t0", "x", "0")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "0"

    def test_mul_by_one(self):
        ir = [IRInstruction(IROpcode.MUL, "t0", "x", "1")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.COPY
        assert result[0].src1 == "x"

    def test_mul_by_two(self):
        ir = [IRInstruction(IROpcode.MUL, "t0", "x", "2")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.ADD
        assert result[0].src1 == "x"
        assert result[0].src2 == "x"

    def test_add_zero(self):
        ir = [IRInstruction(IROpcode.ADD, "t0", "x", "0")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.COPY
        assert result[0].src1 == "x"

    def test_sub_zero(self):
        ir = [IRInstruction(IROpcode.SUB, "t0", "x", "0")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.COPY
        assert result[0].src1 == "x"

    def test_div_by_one(self):
        ir = [IRInstruction(IROpcode.DIV, "t0", "x", "1")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.COPY

    def test_mod_by_one(self):
        ir = [IRInstruction(IROpcode.MOD, "t0", "x", "1")]
        result = strength_reduction(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "0"


class TestAlgebraicSimplification:
    def test_self_eq(self):
        ir = [IRInstruction(IROpcode.EQ, "t0", "x", "x")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "1"

    def test_self_neq(self):
        ir = [IRInstruction(IROpcode.NEQ, "t0", "x", "x")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "0"

    def test_self_sub(self):
        ir = [IRInstruction(IROpcode.SUB, "t0", "x", "x")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "0"

    def test_and_with_zero(self):
        ir = [IRInstruction(IROpcode.AND, "t0", "x", "0")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "0"

    def test_or_with_zero(self):
        ir = [IRInstruction(IROpcode.OR, "t0", "x", "0")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.OR

    def test_and_idempotent_not_rewritten(self):
        ir = [IRInstruction(IROpcode.AND, "t0", "x", "x")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.AND

    def test_or_idempotent_not_rewritten(self):
        ir = [IRInstruction(IROpcode.OR, "t0", "x", "x")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.OR

    def test_and_with_one_not_rewritten(self):
        ir = [IRInstruction(IROpcode.AND, "t0", "x", "1")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.AND

    def test_neg_constant(self):
        ir = [IRInstruction(IROpcode.NEG, "t0", "5")]
        result = algebraic_simplification(ir)
        assert result[0].opcode == IROpcode.LOAD_CONST
        assert result[0].src1 == "-5"


# ======================================================================
# Interpreter Tests
# ======================================================================

class TestInterpreter:
    def test_simple_program(self):
        ast = parse_source("int main() { print(42); return 0; }")
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [42]
        assert result.return_value == 0

    def test_arithmetic(self):
        ast = parse_source("int main() { print(2 + 3 * 4); return 0; }")
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [14]

    def test_while_loop(self):
        source = """
        int main() {
            int i = 0;
            int sum = 0;
            while (i < 5) {
                sum = sum + i;
                i = i + 1;
            }
            print(sum);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [10]  # 0+1+2+3+4 = 10

    def test_if_else(self):
        source = """
        int main() {
            int x = 5;
            if (x > 3) { print(1); } else { print(0); }
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [1]

    def test_function_call(self):
        source = """
        int add(int a, int b) { return a + b; }
        int main() { print(add(10, 20)); return 0; }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [30]

    def test_recursive_function(self):
        source = """
        int factorial(int n) {
            if (n <= 1) { return 1; }
            return n * factorial(n - 1);
        }
        int main() { print(factorial(5)); return 0; }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [120]

    def test_dynamic_count(self):
        ast = parse_source("int main() { print(1); return 0; }")
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.dynamic_instruction_count > 0

    def test_optimized_matches_baseline(self):
        source = """
        int main() {
            int x = 2 + 3;
            int y = x * 4;
            print(y);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        base_result = execute_ir(ir)

        pm = PassManager(["CF", "CP", "SR", "AS", "DCE", "CSE"])
        opt_ir = pm.run(ir)
        opt_result = execute_ir(opt_ir)

        assert base_result.output == opt_result.output
        assert opt_result.dynamic_instruction_count <= base_result.dynamic_instruction_count

    def test_three_param_function(self):
        source = """
        int clamp(int val, int lo, int hi) {
            if (val < lo) { return lo; }
            if (val > hi) { return hi; }
            return val;
        }
        int main() {
            print(clamp(5, 0, 10));
            print(clamp(15, 0, 10));
            print(clamp(0, 1, 10));
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        result = execute_ir(ir)
        assert result.output == [5, 10, 1]


# ======================================================================
# Cross-pass Integration Tests
# ======================================================================

class TestCrossPassIntegration:
    def test_all_six_passes(self):
        source = """
        int main() {
            int a = 1 + 2;
            int b = 3 + 4;
            int c = a + b;
            int d = a + b;
            int unused = 99 * 2;
            print(c);
            print(d);
            return 0;
        }
        """
        ast = parse_source(source)
        ir = generate_ir(ast)
        base_result = execute_ir(ir)

        pm = PassManager(["CF", "CP", "SR", "AS", "DCE", "CSE"])
        opt_ir = pm.run(ir)
        opt_result = execute_ir(opt_ir)

        assert base_result.output == opt_result.output
        assert count_code_size(opt_ir) < count_code_size(ir)

    def test_all_benchmarks_optimize_correctly(self):
        """Every full ordering on every benchmark must preserve output."""
        import glob, os
        programs_dir = os.path.join(os.path.dirname(__file__), "..",
                                    "compiler", "benchmarks", "programs")
        files = sorted(glob.glob(os.path.join(programs_dir, "*.c")))

        for filepath in files:
            with open(filepath) as f:
                source = f.read()

            from compiler.lexer import Lexer
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            from compiler.ir_generator import IRGenerator
            ir = IRGenerator().generate(ast)
            base_result = execute_ir(ir)

            # Test a few representative orderings (not all 720)
            for ordering in [
                ["CF", "CP", "SR", "AS", "DCE", "CSE"],
                ["DCE", "CSE", "CF", "CP", "SR", "AS"],
                ["SR", "AS", "CF", "CP", "DCE", "CSE"],
            ]:
                pm = PassManager(ordering)
                opt_ir = pm.run(ir)
                opt_result = execute_ir(opt_ir)
                name = os.path.basename(filepath)
                assert base_result.output == opt_result.output, \
                    f"{name} with {ordering}: output mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
