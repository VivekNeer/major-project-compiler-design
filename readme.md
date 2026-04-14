# Benchmarking Phase Ordering Trade-offs in a Custom Compiler Infrastructure using MiBench

A complete compiler infrastructure for a C subset language with 6 reorderable optimization passes, an IR interpreter for dynamic metrics, publication-quality benchmarking with MiBench-adapted programs, and an interactive browser-based learning tool.

## Features

### Compiler Pipeline
- **Lexer** -- tokenizer with line/column tracking, single-line and block comments
- **Recursive Descent Parser** -- 6-level operator precedence, full error reporting
- **AST** -- 15 node types as Python dataclasses
- **Three-Address Code IR** -- 27 opcodes with `defined_var()`/`used_vars()` analysis
- **Symbol Table** -- nested scopes with variable shadowing
- **IR Interpreter** -- executes 3AC directly for dynamic instruction counts and output validation

### 6 Optimization Passes

| Pass | Abbr | Description |
|------|------|-------------|
| Constant Folding | CF | Evaluates compile-time constant expressions |
| Dead Code Elimination | DCE | Removes unused assignments and unreachable code |
| Common Subexpression Elimination | CSE | Reuses previously computed expressions |
| Copy Propagation | CP | Substitutes copy chains to enable further optimizations |
| Strength Reduction | SR | Replaces expensive ops with cheaper equivalents (`x*2` -> `x+x`) |
| Algebraic Simplification | AS | Applies identities (`x==x` -> 1, `x&&0` -> 0) |

The **Pass Manager** generates all 721 full permutations for exhaustive phase-ordering analysis.

### 8 MiBench-Adapted Benchmarks

| Program | Source | Characteristic |
|---------|--------|---------------|
| bitcount | MiBench automotive/bitcnts | Loop + conditional + modular arithmetic |
| collatz | MiBench automotive patterns | Unpredictable branching |
| factorial | MiBench basicmath | Multiplication loops + dead code opportunities |
| fibonacci | MiBench basicmath | Iterative loop + variable updates |
| gcd | MiBench basicmath | Euclidean algorithm with modulo |
| isqrt | MiBench automotive/basicmath | Newton's method convergence |
| power | MiBench security/blowfish | Square-and-multiply modular exponentiation |
| sha_mix | MiBench security/sha | Iterative integer mixing with nested conditionals |

### Benchmarking & Visualization
- 3 metric types: static code size, weighted cycle estimate (ARM Cortex-M cost model), dynamic instruction count
- 7 visualization types: Pareto scatter, normalized bars, pass interaction heatmap, category breakdown, reduction heatmap, dynamic vs static, cross-program box plots
- Geometric mean normalization per Fleming & Wallace (1986)
- Correctness validation: every ordering verified against baseline output

### Interactive Learning Tool (Web UI)
- **Learn Mode** -- step-through visualization of every compiler phase (Tokens, AST, Symbol Table, IR, Optimization Diff, Execution)
- **Explore Mode** -- drag-and-drop pass reordering with instant IR updates and metrics
- 8 preloaded benchmark programs
- Dark-themed, zero-dependency frontend served by FastAPI

## Project Structure

```
compiler/
  lexer.py                    # Tokenizer
  parser.py                   # Recursive descent parser
  ast_nodes.py                # AST node definitions
  symbol_table.py             # Scope-aware variable tracking
  ir.py                       # Three-Address Code definitions
  ir_generator.py             # AST -> IR translation
  interpreter.py              # IR interpreter (dynamic execution)
  main.py                     # CLI entry point
  optimizations/
    constant_folding.py       # CF pass
    dead_code_elimination.py  # DCE pass
    common_subexpression_elimination.py  # CSE pass
    copy_propagation.py       # CP pass
    strength_reduction.py     # SR pass
    algebraic_simplification.py  # AS pass
    pass_manager.py           # Configurable pass ordering engine
  benchmarks/
    metric_collector.py       # Static + dynamic metrics
    visualizer.py             # Publication-quality plots (matplotlib)
    programs/                 # 8 MiBench-adapted benchmark programs
  web/
    app.py                    # FastAPI server
    templates.py              # Single-file HTML/CSS/JS frontend
    api_models.py             # Pydantic request/response models
tests/
  test_compiler.py            # 83 compiler tests
  test_web.py                 # 13 web API tests
```

## Setup

### Prerequisites
- Python 3.10+

### Installation

```bash
git clone <repo-url>
cd major-project-compiler-design
pip install -r requirements.txt
```

## Usage

### Compile a program
```bash
python -m compiler.main program.c
```

### Compile with specific optimization passes
```bash
python -m compiler.main program.c --optimize CF,CP,SR,AS,DCE,CSE
```

### Show tokens and AST
```bash
python -m compiler.main program.c --show-tokens --show-ast
```

### Benchmark a single program (all 721 orderings)
```bash
python -m compiler.main program.c --benchmark
```

### Benchmark all 8 programs with full analysis
```bash
python -m compiler.main --benchmark-all --output-dir benchmark_results
```

This generates 54 publication-quality plots and a geometric mean summary table.

### Launch the interactive learning tool
```bash
python -m compiler.web.app
```
Open `http://localhost:8080` in your browser.

## Running Tests

```bash
# All tests (96 total)
python -m pytest -v

# Compiler tests only
python -m pytest tests/test_compiler.py -v

# Web API tests only
python -m pytest tests/test_web.py -v
```

## C Subset Language

The compiler supports a subset of C:

```c
int factorial(int n) {
    int result = 1;
    int i = 1;
    while (i <= n) {
        result = result * i;
        i = i + 1;
    }
    return result;
}

int main() {
    int val = factorial(5);
    print(val);       // outputs: 120
    return 0;
}
```

**Supported constructs:**
- `int` type, integer literals, arithmetic (`+`, `-`, `*`, `/`, `%`)
- Comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), logical (`&&`, `||`, `!`)
- `if`/`else`, `while` loops, block scoping `{ }`
- Functions with parameters, `return`, `print()`
- Single-line (`//`) and block (`/* */`) comments

## Key Research Results

| Program | Baseline | Best Optimized | Code Size Reduction |
|---------|----------|---------------|-------------------|
| factorial | 40 insts | 16 insts | 60.0% |
| isqrt | 50 insts | 27 insts | 46.0% |
| sha_mix | 106 insts | 68 insts | 35.8% |
| power | 71 insts | 47 insts | 33.8% |
| fibonacci | 22 insts | 13 insts | 40.9% |
| bitcount | 33 insts | 19 insts | 42.4% |
| collatz | 42 insts | 26 insts | 38.1% |
| gcd | 21 insts | 14 insts | 33.3% |

**Geometric mean across all programs:** 0.7624 code size ratio (23.8% average reduction).

Best ordering consistently: **CF first** -- Constant Folding enables the most downstream optimization opportunities.

## References

- Guthaus, M.R. et al. "MiBench: A free, commercially representative embedded benchmark suite." IEEE WWC, 2001.
- Cooper, K.D. et al. "Optimizing for Reduced Code Space Using Genetic Algorithms." LCTES, 1999.
- Kulkarni, P. et al. "Exhaustive Optimization Phase Order Space Exploration." CGO, 2006.
- Jain, S. et al. "POSET-RL: Phase Ordering for Optimizing Size and Execution Time using Reinforcement Learning." ISPASS, 2022.
- Fleming, P.J. and Wallace, J.J. "How Not to Lie with Statistics: The Correct Way to Summarize Benchmark Results." CACM, 1986.
