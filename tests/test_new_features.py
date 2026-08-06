"""
Tests for the semantic analyzer, new language features (else-if, for,
short-circuit logic, globals), and the RISC-V RV32IM assembly backend.
"""

import glob
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from compiler.parser import parse_source, ParseError
from compiler.ir_generator import IRGenerator, IRGeneratorError
from compiler.ir import IROpcode
from compiler.interpreter import execute_ir
from compiler.semantic_analyzer import (
    SemanticAnalyzer, SemanticError, check_semantics,
)
from compiler.codegen_riscv import generate_riscv, CodegenError
from compiler.optimizations.pass_manager import PassManager
from riscv_sim import run_assembly

PROGRAMS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "compiler", "benchmarks", "programs"
)

FULL_ORDER = ["CF", "CP", "SR", "AS", "DCE", "CSE"]


def compile_ir(src: str):
    ast = parse_source(src)
    check_semantics(ast)
    return IRGenerator().generate(ast)


# ---------------------------------------------------------------------------
# Semantic analyzer
# ---------------------------------------------------------------------------

class TestSemanticAnalyzer:
    def issues(self, src: str):
        return [str(i) for i in SemanticAnalyzer().analyze(parse_source(src))]

    def test_clean_program_has_no_issues(self):
        assert self.issues("int main() { int x = 1; return x; }") == []

    def test_undeclared_variable(self):
        out = self.issues("int main() { x = 1; return 0; }")
        assert any("Undeclared variable 'x'" in i for i in out)

    def test_undefined_function_call(self):
        out = self.issues("int main() { return foo(); }")
        assert any("undefined function 'foo'" in i for i in out)

    def test_wrong_argument_count(self):
        src = "int f(int a) { return a; } int main() { return f(1, 2); }"
        out = self.issues(src)
        assert any("expects 1 argument" in i for i in out)

    def test_duplicate_declaration_same_scope(self):
        out = self.issues("int main() { int x; int x; return 0; }")
        assert any("already declared" in i for i in out)

    def test_shadowing_in_nested_scope_allowed(self):
        src = "int main() { int x = 1; if (x) { int x = 2; print(x); } return x; }"
        assert self.issues(src) == []

    def test_missing_main(self):
        out = self.issues("int f() { return 1; }")
        assert any("No main()" in i for i in out)

    def test_duplicate_function(self):
        out = self.issues("int f() { return 1; } int f() { return 2; } int main() { return 0; }")
        assert any("more than once" in i for i in out)

    def test_array_used_as_scalar(self):
        out = self.issues("int main() { int a[3]; int x = a; return 0; }")
        assert any("without an index" in i for i in out)

    def test_indexing_a_scalar(self):
        out = self.issues("int main() { int x; x[0] = 1; return 0; }")
        assert any("not an array" in i for i in out)

    def test_global_function_name_conflict(self):
        out = self.issues("int f = 1; int f() { return 1; } int main() { return 0; }")
        assert any("conflicts with a function" in i for i in out)

    def test_nonconstant_global_initializer(self):
        out = self.issues("int g = 1 + 2; int main() { return 0; }")
        assert any("constant expression" in i for i in out)

    def test_all_issues_collected(self):
        src = "int main() { x = 1; y = 2; return foo(); }"
        assert len(self.issues(src)) == 3

    def test_check_semantics_raises(self):
        with pytest.raises(SemanticError):
            check_semantics(parse_source("int main() { x = 1; return 0; }"))

    def test_all_benchmarks_pass_semantics(self):
        for path in sorted(glob.glob(os.path.join(PROGRAMS_DIR, "*.c"))):
            with open(path) as f:
                assert SemanticAnalyzer().analyze(parse_source(f.read())) == []


# ---------------------------------------------------------------------------
# else-if chains
# ---------------------------------------------------------------------------

class TestElseIf:
    def test_else_if_parses_and_runs(self):
        src = """
        int classify(int x) {
            if (x > 100) { return 3; }
            else if (x > 10) { return 2; }
            else if (x > 0) { return 1; }
            else { return 0; }
        }
        int main() {
            print(classify(200)); print(classify(50));
            print(classify(5)); print(classify(-1));
            return 0;
        }
        """
        result = execute_ir(compile_ir(src))
        assert result.output == [3, 2, 1, 0]

    def test_else_still_requires_block_or_if(self):
        with pytest.raises(ParseError):
            parse_source("int main() { if (1) { } else return 0; }")


# ---------------------------------------------------------------------------
# for loops
# ---------------------------------------------------------------------------

class TestForLoop:
    def test_basic_for(self):
        src = """
        int main() {
            int s = 0;
            for (int i = 0; i < 5; i = i + 1) { s = s + i; }
            print(s);
            return s;
        }
        """
        result = execute_ir(compile_ir(src))
        assert result.output == [10]
        assert result.return_value == 10

    def test_for_with_existing_variable(self):
        src = """
        int main() {
            int i;
            int s = 0;
            for (i = 10; i > 0; i = i - 2) { s = s + 1; }
            return s;
        }
        """
        assert execute_ir(compile_ir(src)).return_value == 5

    def test_for_empty_condition_with_break_via_return(self):
        src = """
        int main() {
            int i = 0;
            for (; ; i = i + 1) {
                if (i == 3) { return i; }
            }
            return -1;
        }
        """
        assert execute_ir(compile_ir(src)).return_value == 3

    def test_for_scope_variable_not_visible_outside(self):
        src = """
        int main() {
            for (int i = 0; i < 3; i = i + 1) { print(i); }
            return i;
        }
        """
        with pytest.raises(SemanticError):
            check_semantics(parse_source(src))

    def test_for_orderings_preserve_output(self):
        src = """
        int main() {
            int s = 0;
            for (int i = 1; i <= 10; i = i + 1) { s = s + i * i; }
            print(s);
            return s;
        }
        """
        ir = compile_ir(src)
        base = execute_ir(ir)
        for order in PassManager.all_full_orderings():
            opt = PassManager(order).run(ir) if order else ir
            r = execute_ir(opt)
            assert r.output == base.output
            assert r.return_value == base.return_value


# ---------------------------------------------------------------------------
# Short-circuit evaluation
# ---------------------------------------------------------------------------

class TestShortCircuit:
    SRC = """
    int hits = 0;
    int probe(int v) { hits = hits + 1; return v; }
    int main() {
        int a;
        a = 0 && probe(1);
        print(a); print(hits);
        a = 1 && probe(1);
        print(a); print(hits);
        a = 1 || probe(1);
        print(a); print(hits);
        a = 0 || probe(0);
        print(a); print(hits);
        return 0;
    }
    """

    def test_right_operand_skipped(self):
        result = execute_ir(compile_ir(self.SRC))
        # 0&&: skip probe; 1&&: probe runs; 1||: skip; 0||: probe runs
        assert result.output == [0, 0, 1, 1, 1, 1, 0, 2]

    def test_result_is_normalised_to_0_or_1(self):
        src = "int main() { int x = 7 && 9; int y = 6 || 0; print(x); print(y); return 0; }"
        assert execute_ir(compile_ir(src)).output == [1, 1]

    def test_division_by_zero_guarded_by_short_circuit(self):
        src = """
        int main() {
            int d = 0;
            if (d != 0 && 10 / d > 1) { print(1); } else { print(2); }
            return 0;
        }
        """
        assert execute_ir(compile_ir(src)).output == [2]

    def test_orderings_preserve_short_circuit(self):
        ir = compile_ir(self.SRC)
        base = execute_ir(ir)
        for order in PassManager.all_full_orderings():
            opt = PassManager(order).run(ir) if order else ir
            assert execute_ir(opt).output == base.output


# ---------------------------------------------------------------------------
# Global variables
# ---------------------------------------------------------------------------

class TestGlobals:
    def test_global_read_write_across_functions(self):
        src = """
        int counter = 5;
        int bump() { counter = counter + 1; return counter; }
        int main() {
            print(counter);
            bump(); bump();
            print(counter);
            return counter;
        }
        """
        result = execute_ir(compile_ir(src))
        assert result.output == [5, 7]
        assert result.return_value == 7

    def test_global_default_zero(self):
        src = "int g; int main() { return g; }"
        assert execute_ir(compile_ir(src)).return_value == 0

    def test_negative_constant_initializer(self):
        src = "int g = -3; int main() { return g; }"
        assert execute_ir(compile_ir(src)).return_value == -3

    def test_local_shadows_global(self):
        src = """
        int x = 100;
        int main() { int x = 1; print(x); return 0; }
        """
        assert execute_ir(compile_ir(src)).output == [1]

    def test_global_ir_uses_dedicated_opcodes(self):
        src = "int g = 1; int main() { g = g + 1; return g; }"
        ir = compile_ir(src)
        opcodes = {i.opcode for i in ir}
        assert IROpcode.GLOBAL_DECL in opcodes
        assert IROpcode.GLOBAL_LOAD in opcodes
        assert IROpcode.GLOBAL_STORE in opcodes

    def test_dce_never_removes_global_store(self):
        src = """
        int g = 0;
        int set() { g = 42; return 0; }
        int main() { set(); return g; }
        """
        ir = compile_ir(src)
        for order in PassManager.all_full_orderings():
            opt = PassManager(order).run(ir) if order else ir
            assert execute_ir(opt).return_value == 42

    def test_global_orderings_preserve_output(self):
        src = """
        int acc = 0;
        int add(int v) { acc = acc + v; return acc; }
        int main() {
            for (int i = 0; i < 5; i = i + 1) { add(i * 2); }
            print(acc);
            return acc;
        }
        """
        ir = compile_ir(src)
        base = execute_ir(ir)
        for order in PassManager.all_full_orderings():
            opt = PassManager(order).run(ir) if order else ir
            r = execute_ir(opt)
            assert r.output == base.output
            assert r.return_value == base.return_value


# ---------------------------------------------------------------------------
# RISC-V backend
# ---------------------------------------------------------------------------

class TestRiscvBackend:
    def run_src(self, src: str, order=None):
        ir = compile_ir(src)
        if order:
            ir = PassManager(order).run(ir)
        return run_assembly(generate_riscv(ir))

    def test_structure(self):
        asm = generate_riscv(compile_ir("int main() { return 0; }"))
        assert "    .text" in asm
        assert "_start:" in asm
        assert "main:" in asm
        assert "print_int:" in asm
        assert "li a7, 93" in asm  # exit syscall

    def test_return_value_becomes_exit_code(self):
        assert self.run_src("int main() { return 42; }").exit_code == 42

    def test_print_positive_and_negative(self):
        sim = self.run_src(
            "int main() { print(123); print(0 - 45); print(0); return 0; }"
        )
        assert sim.output_ints == [123, -45, 0]

    def test_arithmetic_and_division_by_zero_semantics(self):
        src = """
        int main() {
            int z = 0;
            print(17 / 5); print(17 % 5);
            print(7 / z); print(7 % z);
            return 0;
        }
        """
        sim = self.run_src(src)
        # x/0 == 0 and x%0 == 0 must match the IR interpreter
        assert sim.output_ints == [3, 2, 0, 0]

    def test_function_calls_and_recursion(self):
        src = """
        int fib(int n) {
            if (n < 2) { return n; }
            return fib(n - 1) + fib(n - 2);
        }
        int main() { print(fib(10)); return 0; }
        """
        assert self.run_src(src).output_ints == [55]

    def test_arrays(self):
        src = """
        int main() {
            int a[10];
            for (int i = 0; i < 10; i = i + 1) { a[i] = i * i; }
            int s = 0;
            for (int i = 0; i < 10; i = i + 1) { s = s + a[i]; }
            print(s);
            return 0;
        }
        """
        assert self.run_src(src).output_ints == [285]

    def test_globals_in_data_section(self):
        src = "int g = 9; int main() { g = g + 1; print(g); return g; }"
        asm = generate_riscv(compile_ir(src))
        assert "    .data" in asm
        assert "g: .word 9" in asm
        sim = self.run_src(src)
        assert sim.output_ints == [10]
        assert sim.exit_code == 10

    def test_too_many_arguments_rejected(self):
        params = ", ".join(f"int p{i}" for i in range(9))
        args = ", ".join("1" for _ in range(9))
        src = f"int f({params}) {{ return p0; }} int main() {{ return f({args}); }}"
        with pytest.raises(CodegenError):
            generate_riscv(compile_ir(src))

    @pytest.mark.parametrize(
        "program",
        sorted(
            os.path.basename(p)
            for p in glob.glob(os.path.join(PROGRAMS_DIR, "*.c"))
        ),
    )
    def test_benchmarks_match_interpreter(self, program):
        with open(os.path.join(PROGRAMS_DIR, program)) as f:
            ir = compile_ir(f.read())
        ref = execute_ir(ir)
        for order in ([], FULL_ORDER):
            opt = PassManager(order).run(ir) if order else ir
            sim = run_assembly(generate_riscv(opt))
            assert sim.output_ints == ref.output, f"{program} {order}"
            assert sim.exit_code == (ref.return_value or 0) & 0xFF or \
                sim.exit_code == ref.return_value, f"{program} {order}"


# ---------------------------------------------------------------------------
# Error hierarchy / driver behaviour
# ---------------------------------------------------------------------------

class TestErrorHierarchy:
    def test_all_phase_errors_share_base(self):
        from compiler.errors import CompilerError
        from compiler.lexer import LexerError
        from compiler.symbol_table import SymbolTableError
        for exc in (LexerError, ParseError, SymbolTableError,
                    IRGeneratorError, SemanticError):
            assert issubclass(exc, CompilerError)

    def test_undeclared_variable_is_semantic_not_crash(self):
        from compiler.main import compile_source
        with pytest.raises(SemanticError):
            compile_source("int main() { x = 1; return 0; }")
