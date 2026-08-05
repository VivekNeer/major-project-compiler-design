# Benchmarking Phase Ordering Trade-offs in a Custom Compiler Infrastructure using MiBench

A complete compiler infrastructure for a C subset language with 6 reorderable optimization passes, a semantic analyzer, an IR interpreter for dynamic metrics, a RISC-V RV32IM assembly backend, publication-quality benchmarking with MiBench-adapted programs, and an interactive browser-based learning tool.

## Features

### Compiler Pipeline

- **Lexer** -- tokenizer with line/column tracking, single-line and block comments
- **Recursive Descent Parser** -- 6-level operator precedence, full error reporting
- **AST** -- 20 node types as Python dataclasses
- **Semantic Analyzer** -- collects *all* violations in one pass: undeclared variables, undefined functions, wrong argument counts, duplicate declarations, array/scalar misuse, non-constant global initializers
- **Three-Address Code IR** -- 35 opcodes with `defined_var()`/`used_vars()` analysis
- **Symbol Table** -- nested scopes with variable shadowing
- **IR Interpreter** -- executes 3AC directly for dynamic instruction counts and output validation
- **RISC-V RV32IM Backend** -- lowers optimized IR to GNU-syntax assembly (Linux user mode), with a built-in `print_int` runtime and interpreter-faithful semantics (`x/0 == 0`); validated by an in-repo RV32IM simulator

### 6 Optimization Passes

| Pass                             | Abbr | Description                                                      |
| -------------------------------- | ---- | ---------------------------------------------------------------- |
| Constant Folding                 | CF   | Evaluates compile-time constant expressions                      |
| Dead Code Elimination            | DCE  | Removes unused assignments and unreachable code                  |
| Common Subexpression Elimination | CSE  | Reuses previously computed expressions                           |
| Copy Propagation                 | CP   | Substitutes copy chains to enable further optimizations          |
| Strength Reduction               | SR   | Replaces expensive ops with cheaper equivalents (`x*2` -> `x+x`) |
| Algebraic Simplification         | AS   | Applies identities (`x==x` -> 1, `x&&0` -> 0)                    |

The **Pass Manager** generates all 721 full permutations for exhaustive phase-ordering analysis.

### 15 MiBench- and PolyBench-Adapted Benchmarks

| Program   | Source                              | Characteristic                                       |
| --------- | ------------------------------------ | ----------------------------------------------------- |
| bitcount  | MiBench automotive/bitcnts           | Loop + conditional + modular arithmetic                |
| collatz   | MiBench automotive patterns          | Unpredictable branching                                |
| factorial | MiBench basicmath                    | Multiplication loops + dead code opportunities         |
| fibonacci | MiBench basicmath                    | Iterative loop + variable updates                      |
| gcd       | MiBench basicmath                    | Euclidean algorithm with modulo                        |
| isqrt     | MiBench automotive/basicmath         | Newton's method convergence                            |
| power     | MiBench security/blowfish            | Square-and-multiply modular exponentiation              |
| sha_mix   | MiBench security/sha                 | Iterative integer mixing with nested conditionals       |
| jacobi1d  | PolyBench/C stencils/jacobi-1d       | Array load/store, index arithmetic, nested loops        |
| jacobi2d  | PolyBench/C stencils/jacobi-2d       | Flattened 2D stencil, five-point read pattern           |
| gemm      | PolyBench/C linear-algebra/blas/gemm | Triple-nested loop, flattened matrix multiply-accumulate |
| 2mm       | PolyBench/C linear-algebra/kernels/2mm | Two chained matrix multiplications, five live arrays   |
| atax      | PolyBench/C linear-algebra/kernels/atax | Two sequential reduction loops sharing an intermediate array |
| bicg      | PolyBench/C linear-algebra/kernels/bicg | Two accumulators updated from one shared matrix load  |
| gesummv   | PolyBench/C linear-algebra/blas/gesummv | Two matrix-vector products combined by a scalar step |

### Benchmarking & Visualization

- 3 metric types: static code size, weighted cycle estimate (ARM Cortex-M cost model), dynamic instruction count
- 7 visualization types: Pareto scatter, normalized bars, pass interaction heatmap, category breakdown, reduction heatmap, dynamic vs static, cross-program box plots
- Geometric mean normalization per Fleming & Wallace (1986)
- Correctness validation: every ordering verified against baseline output

### Interactive Web Application (React + FastAPI)

- **Playground** -- CodeMirror editor with semantic-error squiggles; inspect tokens, collapsible AST tree, symbol table, and IR
- **Optimization Lab** -- drag-and-drop pass ordering with a per-pass stepping timeline: watch the IR shrink stage by stage with diffs and metric deltas
- **Assembly** -- side-by-side IR and RISC-V output with hover-linked line mapping
- **Phase-Ordering Explorer** -- runs all 721 orderings in the browser; interactive Pareto scatter (click a point for details) and top-orderings chart
- **Reference** -- pass catalog, cost model, and language guide
- 15 preloaded benchmark programs; legacy zero-dependency page still served at `/legacy`

## Project Structure

```text
compiler/
  lexer.py                    # Tokenizer
  parser.py                   # Recursive descent parser
  ast_nodes.py                # AST node definitions
  errors.py                   # Shared CompilerError exception hierarchy
  semantic_analyzer.py        # Semantic checks between parse and IR gen
  symbol_table.py             # Scope-aware variable tracking
  ir.py                       # Three-Address Code definitions
  ir_generator.py             # AST -> IR translation
  interpreter.py              # IR interpreter (dynamic execution)
  codegen_riscv.py            # RISC-V RV32IM assembly backend
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
    programs/                 # 15 MiBench- and PolyBench-adapted benchmark programs
  web/
    app.py                    # FastAPI server (API + static frontend)
    templates.py              # Legacy single-file frontend (/legacy)
    api_models.py             # Pydantic request/response models
    static/                   # Built React app (from frontend/)
frontend/                     # React + Vite + TypeScript source
tests/
  test_compiler.py            # 101 compiler tests
  test_web.py                 # 21 web API tests
  test_new_features.py        # 58 semantic / language-feature / codegen tests
  riscv_sim.py                # Minimal RV32IM simulator (test oracle for the backend)
```

## Setup

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/VivekNeer/major-project-compiler-design.git
cd major-project-compiler-design
pip install -r requirements.txt
```

## Usage

### Compile a program

```bash
python -m compiler.main compiler/benchmarks/programs/factorial.c
```

### Compile with specific optimization passes

```bash
python -m compiler.main compiler/benchmarks/programs/factorial.c --optimize CF,CP,SR,AS,DCE,CSE
```

### Show tokens and AST

```bash
python -m compiler.main compiler/benchmarks/programs/factorial.c --show-tokens --show-ast
```

### Benchmark a single program (all 721 orderings)

```bash
python -m compiler.main compiler/benchmarks/programs/factorial.c --benchmark
```

### Benchmark all 15 programs with full analysis

```bash
python -m compiler.main --benchmark-all --output-dir benchmark_results
```

This generates 91 publication-quality plots (6 per program plus one cross-program box plot) and a geometric mean summary table.

### Emit RISC-V RV32IM assembly

```bash
# To stdout
python -m compiler.main compiler/benchmarks/programs/factorial.c --optimize CF,CP,SR,AS,DCE,CSE --emit-asm

# To a file
python -m compiler.main compiler/benchmarks/programs/factorial.c -O CF,DCE -S factorial.s
```

The output is GNU-syntax RV32IM assembly for Linux user mode. To run it
on real tooling (optional — the test suite validates it with a bundled
simulator):

```bash
sudo apt install gcc-riscv64-linux-gnu qemu-user
riscv64-linux-gnu-gcc -march=rv32im -mabi=ilp32 -static -nostdlib -o factorial factorial.s
qemu-riscv32 ./factorial
```

### Launch the interactive web application

```bash
python -m compiler.web.app
```

Open `http://localhost:8080` in your browser. The prebuilt React app in
`compiler/web/static/` is served automatically; the legacy single-file UI
remains at `http://localhost:8080/legacy`.

To develop the frontend (requires Node 20+):

```bash
cd frontend
npm install
npm run dev      # dev server on :5173, proxies /api to :8080
npm run build    # rebuilds compiler/web/static/
```

## Running Tests

```bash
# All tests (180 total)
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
- Global variables (`int g = 5;` at file scope, constant initializers, stored in `.data` in the RISC-V backend)
- Fixed-size 1D arrays (`int a[10];`), zero-initialised, with indexed load/store (`a[i]`, `a[i] = expr;`)
- Comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), logical (`&&`, `||`, `!`) with **C short-circuit evaluation**
- `if`/`else`/`else if` chains, `while` and `for` loops, block scoping `{ }`
- Functions with parameters, `return`, `print()`
- Single-line (`//`) and block (`/* */`) comments

## Key Research Results

| Program   | Baseline  | Best Optimized | Code Size Reduction |
| --------- | --------- | -------------- | ------------------- |
| factorial | 40 insts  | 16 insts       | 60.0%               |
| isqrt     | 50 insts  | 27 insts       | 46.0%               |
| sha_mix   | 106 insts | 68 insts       | 35.8%               |
| power     | 71 insts  | 47 insts       | 33.8%               |
| fibonacci | 22 insts  | 13 insts       | 40.9%               |
| bitcount  | 33 insts  | 19 insts       | 42.4%               |
| collatz   | 42 insts  | 26 insts       | 38.1%               |
| gcd       | 21 insts  | 14 insts       | 33.3%               |

**Geometric mean across all programs:** 0.7624 code size ratio (23.8% average reduction).

Best ordering consistently: **CF first** -- Constant Folding enables the most downstream optimization opportunities.

## References

- Guthaus, M.R. et al. "MiBench: A free, commercially representative embedded benchmark suite." IEEE WWC, 2001.
- Cooper, K.D. et al. "Optimizing for Reduced Code Space Using Genetic Algorithms." LCTES, 1999.
- Kulkarni, P. et al. "Exhaustive Optimization Phase Order Space Exploration." CGO, 2006.
- Jain, S. et al. "POSET-RL: Phase Ordering for Optimizing Size and Execution Time using Reinforcement Learning." ISPASS, 2022.
- Fleming, P.J. and Wallace, J.J. "How Not to Lie with Statistics: The Correct Way to Summarize Benchmark Results." CACM, 1986.
