"""
Compiler CLI -- main entry point.

Usage:
    python -m compiler.main <source.c>                        # compile & show IR
    python -m compiler.main <source.c> --optimize CF,DCE      # compile with specific passes
    python -m compiler.main <source.c> --benchmark            # run all orderings & visualise
    python -m compiler.main --benchmark-all                   # benchmark all programs
"""

from __future__ import annotations
import argparse
import glob
import os
import sys

from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParseError
from compiler.ir_generator import IRGenerator, IRGeneratorError
from compiler.ir import format_ir
from compiler.interpreter import execute_ir, InterpreterError
from compiler.optimizations.pass_manager import PassManager, PASS_REGISTRY, PASS_NAMES
from compiler.benchmarks.metric_collector import (
    collect_metrics, BenchmarkMetrics, count_code_size, estimate_cycles,
)
from compiler.benchmarks.visualizer import (
    generate_all_plots, compute_geomean_summary,
)


def compile_source(source: str, pass_order: list[str] | None = None):
    """Full compilation pipeline. Returns (ast, base_ir, optimized_ir)."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)

    if pass_order:
        optimized = PassManager(pass_order).run(ir)
    else:
        optimized = ir

    return ast, ir, optimized


def run_benchmark(
    source: str,
    program_name: str = "",
    output_dir: str = "benchmark_results",
) -> list[BenchmarkMetrics]:
    """Run all full-length pass orderings, collect static + dynamic metrics."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    base_ir = IRGenerator().generate(ast)

    # Execute baseline for output validation
    base_exec = execute_ir(base_ir)

    # Use full orderings (all 6 passes in every permutation) + baseline
    orderings = PassManager.all_full_orderings()
    results: list[BenchmarkMetrics] = []

    for ordering in orderings:
        pm = PassManager(ordering)
        optimized = pm.run(base_ir)

        # Dynamic execution
        try:
            exec_result = execute_ir(optimized)
            dyn_count = exec_result.dynamic_instruction_count
            dyn_freq = exec_result.opcode_frequency
            correct = exec_result.output == base_exec.output
        except (InterpreterError, RecursionError):
            dyn_count = 0
            dyn_freq = {}
            correct = False

        metrics = collect_metrics(
            optimized, ordering,
            dynamic_instruction_count=dyn_count,
            dynamic_opcode_frequency=dyn_freq,
            output_correct=correct,
        )
        results.append(metrics)

    return results


def print_metrics_table(results: list[BenchmarkMetrics]) -> None:
    """Pretty-print a comparison table with static and dynamic metrics."""
    has_dyn = any(r.dynamic_instruction_count > 0 for r in results)

    if has_dyn:
        hdr = f"  {'Pass Ordering':<40} {'Size':>6} {'Cycles':>8} {'Dyn Insts':>10} {'OK':>4}"
        print(f"\n{hdr}")
        print("  " + "-" * 72)
        for r in sorted(results, key=lambda r: r.code_size):
            ok = "Y" if r.output_correct else "N"
            print(f"  {r.pass_order_label:<40} {r.code_size:>6} "
                  f"{r.estimated_cycles:>8.0f} {r.dynamic_instruction_count:>10} {ok:>4}")
    else:
        print(f"\n  {'Pass Ordering':<40} {'Size':>6} {'Cycles':>10}")
        print("  " + "-" * 60)
        for r in sorted(results, key=lambda r: r.code_size):
            print(f"  {r.pass_order_label:<40} {r.code_size:>6} "
                  f"{r.estimated_cycles:>10.1f}")


def print_geomean_table(summary: dict[str, dict[str, float]]) -> None:
    """Print geometric mean summary across programs."""
    print(f"\n  {'Ordering':<40} {'Size':>8} {'Cycles':>8} {'Dynamic':>8}")
    print("  " + "-" * 68)
    for label in sorted(summary.keys(), key=lambda k: summary[k]["geomean_size"]):
        s = summary[label]
        print(f"  {label:<40} {s['geomean_size']:>8.4f} "
              f"{s['geomean_cycles']:>8.4f} {s['geomean_dynamic']:>8.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Custom Compiler Infrastructure for Phase-Ordering Benchmarking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available passes: {', '.join(f'{k} ({v})' for k, v in PASS_NAMES.items())}

Examples:
  python -m compiler.main program.c
  python -m compiler.main program.c --optimize CF,CP,DCE,CSE,SR,AS
  python -m compiler.main program.c --benchmark
  python -m compiler.main --benchmark-all
        """,
    )
    parser.add_argument("source", nargs="?", help="Source file to compile")
    parser.add_argument(
        "--optimize", "-O",
        help="Comma-separated list of passes: " + ", ".join(PASS_REGISTRY.keys()),
    )
    parser.add_argument(
        "--benchmark", "-b", action="store_true",
        help="Run all full-length pass orderings with static + dynamic metrics",
    )
    parser.add_argument(
        "--benchmark-all", "-B", action="store_true",
        help="Benchmark all programs in benchmarks/programs/",
    )
    parser.add_argument(
        "--output-dir", "-o", default="benchmark_results",
        help="Output directory for benchmark results (default: benchmark_results)",
    )
    parser.add_argument("--show-tokens", action="store_true")
    parser.add_argument("--show-ast", action="store_true")

    args = parser.parse_args()

    # --- Benchmark all programs ---
    if args.benchmark_all:
        programs_dir = os.path.join(os.path.dirname(__file__), "benchmarks", "programs")
        files = sorted(glob.glob(os.path.join(programs_dir, "*.c")))
        if not files:
            print(f"No .c files found in {programs_dir}")
            sys.exit(1)

        all_results: dict[str, list[BenchmarkMetrics]] = {}
        for filepath in files:
            name = os.path.splitext(os.path.basename(filepath))[0]
            print(f"\n{'='*60}")
            print(f"  Benchmarking: {name}")
            print(f"{'='*60}")

            with open(filepath, "r") as f:
                source = f.read()

            try:
                results = run_benchmark(source, program_name=name,
                                        output_dir=args.output_dir)
                # Print only top-10 and bottom-5 by size for readability
                sorted_results = sorted(results, key=lambda r: r.code_size)
                print_metrics_table(sorted_results[:10])
                all_results[name] = results
            except (LexerError, ParseError, IRGeneratorError) as e:
                print(f"  ERROR: {e}")

        # Generate per-program and cross-program plots
        for name, results in all_results.items():
            try:
                paths = generate_all_plots(
                    results, output_dir=args.output_dir,
                    program_name=name, all_program_results=all_results,
                )
            except ImportError:
                pass

        # Generate cross-program box plot once
        try:
            from compiler.benchmarks.visualizer import plot_box_distributions
            plot_box_distributions(
                all_results,
                output_path=os.path.join(args.output_dir, "cross_program_box.png"),
            )
        except ImportError:
            pass

        # Correctness check
        all_correct = True
        for name, results in all_results.items():
            for r in results:
                if not r.output_correct:
                    print(f"\n  WARNING: {name} ordering {r.pass_order_label} "
                          f"produced incorrect output!")
                    all_correct = False
        if all_correct:
            print(f"\n  All orderings produce correct output across all programs.")

        # Geometric mean summary
        summary = compute_geomean_summary(all_results)
        print(f"\n{'='*60}")
        print("  GEOMETRIC MEAN (normalized to baseline = 1.0)")
        print(f"{'='*60}")
        print_geomean_table(summary)

        # Best per program
        print(f"\n{'='*60}")
        print("  BEST ORDERING PER PROGRAM")
        print(f"{'='*60}")
        for name, results in all_results.items():
            best_size = min(results, key=lambda r: r.code_size)
            best_dyn = min(results, key=lambda r: r.dynamic_instruction_count) \
                if any(r.dynamic_instruction_count > 0 for r in results) else best_size
            print(f"\n  {name}:")
            print(f"    Best static size:  {best_size.pass_order_label} "
                  f"({best_size.code_size} insts)")
            print(f"    Best dynamic:      {best_dyn.pass_order_label} "
                  f"({best_dyn.dynamic_instruction_count} dyn insts)")

        print(f"\n  Plots saved to {args.output_dir}/")
        return

    # --- Single file ---
    if not args.source:
        parser.print_help()
        sys.exit(1)

    with open(args.source, "r") as f:
        source = f.read()

    if args.show_tokens:
        tokens = Lexer(source).tokenize()
        print("\n  Token Stream:")
        for tok in tokens:
            print(f"  {tok}")
        print()

    if args.show_ast:
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        print("\n  AST:")
        _print_ast(ast, indent=2)
        print()

    if args.benchmark:
        name = os.path.splitext(os.path.basename(args.source))[0]
        results = run_benchmark(source, program_name=name,
                                output_dir=args.output_dir)
        print_metrics_table(results)
        try:
            paths = generate_all_plots(results, output_dir=args.output_dir,
                                       program_name=name)
            print(f"\n  Plots saved to {args.output_dir}/")
        except ImportError:
            pass
        return

    # Normal compilation
    pass_order = args.optimize.split(",") if args.optimize else None
    try:
        ast, base_ir, optimized_ir = compile_source(source, pass_order)
    except (LexerError, ParseError, IRGeneratorError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n  === Unoptimized IR ===")
    print(format_ir(base_ir))

    if pass_order:
        pm = PassManager(pass_order)
        print(f"\n  === Optimized IR ({pm.describe()}) ===")
        print(format_ir(optimized_ir))

        base_size = count_code_size(base_ir)
        opt_size = count_code_size(optimized_ir)
        base_cycles = estimate_cycles(base_ir)
        opt_cycles = estimate_cycles(optimized_ir)

        print(f"\n  === Metrics ===")
        if base_size > 0:
            print(f"  Code size:  {base_size} -> {opt_size} "
                  f"({(1 - opt_size/base_size)*100:.1f}% reduction)")
        if base_cycles > 0:
            print(f"  Est cycles: {base_cycles:.0f} -> {opt_cycles:.0f} "
                  f"({(1 - opt_cycles/base_cycles)*100:.1f}% reduction)")

        # Dynamic validation
        try:
            base_exec = execute_ir(base_ir)
            opt_exec = execute_ir(optimized_ir)
            print(f"  Dynamic:    {base_exec.dynamic_instruction_count} -> "
                  f"{opt_exec.dynamic_instruction_count} instructions")
            if base_exec.output == opt_exec.output:
                print(f"  Output:     CORRECT (matches baseline)")
            else:
                print(f"  Output:     MISMATCH!")
                print(f"    Baseline: {base_exec.output}")
                print(f"    Optimized: {opt_exec.output}")
        except (InterpreterError, RecursionError) as e:
            print(f"  Interpreter: {e}")


def _print_ast(node, indent=0):
    prefix = " " * indent
    name = type(node).__name__
    fields = {}
    for key, val in node.__dict__.items():
        if key in ("line", "col"):
            continue
        if isinstance(val, list):
            fields[key] = f"[{len(val)} items]"
        elif hasattr(val, "__dict__") and hasattr(val, "line"):
            fields[key] = type(val).__name__
        else:
            fields[key] = repr(val)
    field_str = ", ".join(f"{k}={v}" for k, v in fields.items())
    print(f"{prefix}{name}({field_str})")
    for key, val in node.__dict__.items():
        if key in ("line", "col"):
            continue
        if isinstance(val, list):
            for item in val:
                if hasattr(item, "__dict__") and hasattr(item, "line"):
                    _print_ast(item, indent + 2)
        elif hasattr(val, "__dict__") and hasattr(val, "line"):
            _print_ast(val, indent + 2)


if __name__ == "__main__":
    main()
