# Interactive Compiler Learning Tool — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a browser-based interactive learning tool that visualizes every compiler phase and lets students experiment with optimization pass orderings.

**Architecture:** FastAPI backend wrapping existing compiler modules, serving a single-file HTML/CSS/JS frontend. Two modes: Learn (step-through) and Explore (playground). No JS build step, no external dependencies.

**Tech Stack:** Python 3.14, FastAPI, uvicorn, vanilla HTML/CSS/JS

**Spec:** `docs/superpowers/specs/2026-04-14-interactive-learning-tool-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `compiler/ir_generator.py` | Modify | Add `generate_with_symbols()` method |
| `compiler/web/__init__.py` | Create | Empty package init |
| `compiler/web/api_models.py` | Create | Pydantic request/response schemas |
| `compiler/web/app.py` | Create | FastAPI server, all routes, serialization helpers |
| `compiler/web/templates.py` | Create | Complete HTML/CSS/JS frontend as Python string |
| `tests/test_web.py` | Create | API endpoint tests |
| `requirements.txt` | Modify | Add fastapi, uvicorn |

---

### Task 1: Add `generate_with_symbols()` to IRGenerator

**Files:**
- Modify: `compiler/ir_generator.py`
- Test: `tests/test_compiler.py`

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_compiler.py, class TestIRGenerator

def test_generate_with_symbols(self):
    ast = parse_source("""
    int add(int a, int b) {
        int result = a + b;
        return result;
    }
    int main() {
        int x = add(3, 4);
        print(x);
        return 0;
    }
    """)
    from compiler.ir_generator import IRGenerator
    gen = IRGenerator()
    ir, symbols = gen.generate_with_symbols(ast)
    assert len(ir) > 0
    names = [s["name"] for s in symbols]
    assert "a" in names
    assert "b" in names
    assert "result" in names
    assert "x" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_compiler.py::TestIRGenerator::test_generate_with_symbols -v`
Expected: FAIL with `AttributeError: 'IRGenerator' object has no attribute 'generate_with_symbols'`

- [ ] **Step 3: Implement `generate_with_symbols()`**

In `compiler/ir_generator.py`, add to the `IRGenerator` class:

```python
def __init__(self) -> None:
    self._instructions: list[IRInstruction] = []
    self._temp_counter: int = 0
    self._label_counter: int = 0
    self._symtab = SymbolTable()
    self._all_symbols: list[dict] = []  # <-- ADD THIS LINE

def generate_with_symbols(self, program: Program) -> tuple[list[IRInstruction], list[dict]]:
    """Generate IR and return accumulated symbol info."""
    self._all_symbols = []
    instructions = self.generate(program)
    return instructions, self._all_symbols
```

Then in `_gen_var_decl`, after `sym = self._symtab.declare(node.name)`, add:
```python
self._all_symbols.append({
    "name": sym.name, "type": sym.var_type,
    "scope": sym.scope_depth, "ir_name": sym.ir_name,
})
```

And in `_gen_function`, after the param `self._symtab.declare(param.name)` line, add:
```python
self._all_symbols.append({
    "name": sym.name, "type": "int",
    "scope": sym.scope_depth, "ir_name": sym.ir_name,
})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_compiler.py::TestIRGenerator::test_generate_with_symbols -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to ensure no regressions**

Run: `python -m pytest tests/test_compiler.py -v`
Expected: All 84 tests PASS

- [ ] **Step 6: Commit**

```bash
git add compiler/ir_generator.py tests/test_compiler.py
git commit -m "feat: add generate_with_symbols() to IRGenerator"
```

---

### Task 2: Create Pydantic API Models

**Files:**
- Create: `compiler/web/__init__.py`
- Create: `compiler/web/api_models.py`

- [ ] **Step 1: Create the web package**

Create `compiler/web/__init__.py` (empty file).

- [ ] **Step 2: Write `api_models.py`**

```python
"""Pydantic request/response models for the web API."""
from __future__ import annotations
from pydantic import BaseModel


class CompileRequest(BaseModel):
    source: str

class OptimizeRequest(BaseModel):
    source: str
    pass_order: list[str]

class BenchmarkRequest(BaseModel):
    source: str

class TokenInfo(BaseModel):
    type: str
    value: str
    line: int
    col: int

class ASTNodeInfo(BaseModel):
    type: str
    name: str | None = None
    fields: dict = {}
    line: int = 0
    col: int = 0
    children: list[ASTNodeInfo] = []

class SymbolInfo(BaseModel):
    name: str
    type: str
    scope: int
    ir_name: str

class IRInstructionInfo(BaseModel):
    opcode: str
    dest: str | None = None
    src1: str | None = None
    src2: str | None = None

class DiffLine(BaseModel):
    type: str   # "kept", "added", "removed"
    text: str

class MetricsInfo(BaseModel):
    code_size: int
    estimated_cycles: float
    dynamic_count: int

class CompileResponse(BaseModel):
    tokens: list[TokenInfo]
    ast: dict  # recursive, use dict not ASTNodeInfo to avoid depth issues
    symbols: list[SymbolInfo]
    ir: list[IRInstructionInfo]
    ir_text: str

class OptimizeResponse(BaseModel):
    pass_order: list[str]
    optimized_ir: list[IRInstructionInfo]
    optimized_ir_text: str
    diff: list[DiffLine]
    metrics: MetricsInfo
    output: list[int]
    output_correct: bool
    explanation: str

class BenchmarkResult(BaseModel):
    pass_order: list[str]
    label: str
    code_size: int
    estimated_cycles: float
    dynamic_count: int
    output_correct: bool

class BenchmarkResponse(BaseModel):
    results: list[BenchmarkResult]
    baseline: BenchmarkResult

class ErrorResponse(BaseModel):
    error: bool = True
    phase: str
    message: str
    line: int | None = None
    col: int | None = None

class ExampleInfo(BaseModel):
    name: str
    description: str

class ExampleSource(BaseModel):
    name: str
    source: str
```

- [ ] **Step 3: Verify import works**

Run: `python -c "from compiler.web.api_models import CompileRequest; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add compiler/web/__init__.py compiler/web/api_models.py
git commit -m "feat: add Pydantic API models for web interface"
```

---

### Task 3: Build the FastAPI Server

**Files:**
- Create: `compiler/web/app.py`
- Test: `tests/test_web.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Add to `requirements.txt`:
```
fastapi>=0.100
uvicorn>=0.20
```

Run: `pip install fastapi uvicorn`

- [ ] **Step 2: Write API tests**

Create `tests/test_web.py`:

```python
"""Tests for the web API endpoints."""
import pytest
from fastapi.testclient import TestClient
from compiler.web.app import app

client = TestClient(app)

SIMPLE_PROGRAM = "int main() { int x = 2 + 3; print(x); return 0; }"
BAD_PROGRAM = "int main( { }"

class TestCompileEndpoint:
    def test_compile_success(self):
        resp = client.post("/api/compile", json={"source": SIMPLE_PROGRAM})
        assert resp.status_code == 200
        data = resp.json()
        assert "tokens" in data
        assert "ast" in data
        assert "symbols" in data
        assert "ir" in data
        assert "ir_text" in data
        assert len(data["tokens"]) > 0
        assert data["ast"]["type"] == "Program"

    def test_compile_error(self):
        resp = client.post("/api/compile", json={"source": BAD_PROGRAM})
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is True
        assert data["phase"] == "parser"
        assert "line" in data

class TestOptimizeEndpoint:
    def test_optimize_success(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": ["CF", "DCE"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "optimized_ir_text" in data
        assert "metrics" in data
        assert "diff" in data
        assert data["output_correct"] is True

    def test_optimize_invalid_pass(self):
        resp = client.post("/api/optimize", json={
            "source": SIMPLE_PROGRAM,
            "pass_order": ["INVALID"]
        })
        data = resp.json()
        assert data["error"] is True

class TestExamplesEndpoint:
    def test_list_examples(self):
        resp = client.get("/api/examples")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8
        names = [e["name"] for e in data]
        assert "fibonacci" in names
        assert "factorial" in names

    def test_get_example(self):
        resp = client.get("/api/examples/fibonacci")
        assert resp.status_code == 200
        data = resp.json()
        assert "source" in data
        assert "int main()" in data["source"]

    def test_get_nonexistent_example(self):
        resp = client.get("/api/examples/nonexistent")
        assert resp.status_code == 404

class TestBenchmarkEndpoint:
    def test_benchmark(self):
        source = "int main() { int x = 2 + 3; print(x); return 0; }"
        resp = client.post("/api/benchmark", json={"source": source})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "baseline" in data
        assert len(data["results"]) > 1  # baseline + orderings

class TestIndexPage:
    def test_serves_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_html_contains_key_elements(self):
        resp = client.get("/")
        html = resp.text
        assert 'id="learn-mode"' in html
        assert 'id="explore-mode"' in html
        assert "compile()" in html or "compile(" in html
        assert "optimize(" in html
        assert "Compiler Explorer" in html
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_web.py -v`
Expected: FAIL (app not created yet)

- [ ] **Step 4: Implement `compiler/web/app.py`**

Build the complete FastAPI application. Here are the key helper functions and route skeletons:

```python
"""FastAPI web server for the interactive compiler learning tool."""
from __future__ import annotations
import difflib
import glob
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParseError
from compiler.ir_generator import IRGenerator, IRGeneratorError
from compiler.ir import format_ir
from compiler.interpreter import execute_ir
from compiler.optimizations.pass_manager import PassManager
from compiler.benchmarks.metric_collector import count_code_size, estimate_cycles
from compiler.web.api_models import *
from compiler.web.templates import INDEX_HTML

app = FastAPI(title="Compiler Explorer")

PROGRAMS_DIR = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "programs")

# --- AST Serialization ---
def serialize_ast(node) -> dict:
    """Recursively serialize an AST node to a JSON-compatible dict."""
    from compiler.ast_nodes import ASTNode
    result = {"type": type(node).__name__, "line": getattr(node, "line", 0),
              "col": getattr(node, "col", 0), "fields": {}, "children": []}
    for key, val in node.__dict__.items():
        if key in ("line", "col"):
            continue
        if isinstance(val, ASTNode):
            result["children"].append(serialize_ast(val))
        elif isinstance(val, list) and val and isinstance(val[0], ASTNode):
            for item in val:
                result["children"].append(serialize_ast(item))
        else:
            result["fields"][key] = val
    return result

# --- IR Diff ---
def compute_diff(before_text: str, after_text: str) -> list[dict]:
    """Line-based diff of IR text, returns list of {type, text}."""
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()
    diff_result = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, before_lines, after_lines
    ).get_opcodes():
        if tag == "equal":
            for line in before_lines[i1:i2]:
                diff_result.append({"type": "kept", "text": line})
        elif tag == "delete":
            for line in before_lines[i1:i2]:
                diff_result.append({"type": "removed", "text": line})
        elif tag == "insert":
            for line in after_lines[j1:j2]:
                diff_result.append({"type": "added", "text": line})
        elif tag == "replace":
            for line in before_lines[i1:i2]:
                diff_result.append({"type": "removed", "text": line})
            for line in after_lines[j1:j2]:
                diff_result.append({"type": "added", "text": line})
    return diff_result

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML

@app.post("/api/compile")
def compile_source(req: CompileRequest):
    try:
        tokens = Lexer(req.source).tokenize()
    except LexerError as e:
        return {"error": True, "phase": "lexer", "message": str(e),
                "line": e.line, "col": e.col}
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        return {"error": True, "phase": "parser", "message": str(e),
                "line": e.token.line, "col": e.token.col}
    try:
        gen = IRGenerator()
        ir, symbols = gen.generate_with_symbols(ast)
    except IRGeneratorError as e:
        return {"error": True, "phase": "ir_generator", "message": str(e),
                "line": None, "col": None}
    return {
        "tokens": [{"type": t.type.name, "value": t.value,
                     "line": t.line, "col": t.col} for t in tokens if t.type.name != "EOF"],
        "ast": serialize_ast(ast),
        "symbols": symbols,
        "ir": [{"opcode": i.opcode.name, "dest": i.dest,
                "src1": i.src1, "src2": i.src2} for i in ir],
        "ir_text": format_ir(ir),
    }

@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    try:
        tokens = Lexer(req.source).tokenize()
        ast = Parser(tokens).parse()
        base_ir = IRGenerator().generate(ast)
        pm = PassManager(req.pass_order)
        opt_ir = pm.run(base_ir)
    except (LexerError, ParseError, IRGeneratorError, ValueError) as e:
        phase = type(e).__name__.replace("Error", "").lower()
        line = getattr(e, "line", None) or getattr(getattr(e, "token", None), "line", None)
        col = getattr(e, "col", None) or getattr(getattr(e, "token", None), "col", None)
        return {"error": True, "phase": phase, "message": str(e), "line": line, "col": col}

    base_text = format_ir(base_ir)
    opt_text = format_ir(opt_ir)
    diff = compute_diff(base_text, opt_text)

    removed = sum(1 for d in diff if d["type"] == "removed")
    added = sum(1 for d in diff if d["type"] == "added")
    explanation = f"Removed {removed} instructions, added {added}. Net reduction: {removed - added}."

    base_exec = execute_ir(base_ir)
    opt_exec = execute_ir(opt_ir)

    return {
        "pass_order": req.pass_order,
        "optimized_ir": [{"opcode": i.opcode.name, "dest": i.dest,
                          "src1": i.src1, "src2": i.src2} for i in opt_ir],
        "optimized_ir_text": opt_text,
        "diff": diff,
        "metrics": {"code_size": count_code_size(opt_ir),
                    "estimated_cycles": estimate_cycles(opt_ir),
                    "dynamic_count": opt_exec.dynamic_instruction_count},
        "output": opt_exec.output,
        "output_correct": base_exec.output == opt_exec.output,
        "explanation": explanation,
    }

# ... similarly implement /api/benchmark, /api/examples, /api/examples/{name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

The `/api/benchmark` endpoint follows the same pattern: compile, run `PassManager.all_full_orderings()`, collect metrics + dynamic counts for each, return as list.

The `/api/examples` endpoint scans `PROGRAMS_DIR` for `*.c` files and returns name + first comment line as description. `/api/examples/{name}` reads the specific file or returns 404.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_web.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests PASS (both test_compiler.py and test_web.py)

- [ ] **Step 7: Commit**

```bash
git add compiler/web/app.py tests/test_web.py requirements.txt
git commit -m "feat: add FastAPI server with compile, optimize, benchmark, examples endpoints"
```

---

### Task 4: Build the Frontend — Learn Mode

**Files:**
- Create: `compiler/web/templates.py`

- [ ] **Step 1: Create `templates.py` with the HTML skeleton**

Build the complete single-page application as a Python string in `templates.py`. The file exports one constant: `INDEX_HTML`.

**HTML structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Compiler Explorer</title>
  <style>/* ~400 lines: dark theme, panels, tokens, AST tree, diff, chips */</style>
</head>
<body>
  <header><!-- Mode toggle: Learn | Explore, Examples dropdown --></header>
  <main id="learn-mode">
    <!-- Step indicators: Source | Tokens | AST | Symbols | IR | Optimize | Execute -->
    <!-- Step content area (one visible at a time) -->
    <!-- Code editor (always visible in sidebar) -->
    <!-- Navigation: Previous / Next / Compile buttons -->
  </main>
  <main id="explore-mode" style="display:none">
    <!-- Left: editor, Center: IR view, Right: metrics -->
    <!-- Bottom: pass ordering toolbar with draggable chips -->
  </main>
  <script>/* ~500 lines: API calls, step navigation, drag-drop, diff rendering */</script>
</body>
</html>
```

**CSS key sections (dark theme):**
- Base: `background: #1e1e2e`, `color: #cdd6f4`, monospace fonts
- Code editor: dark textarea with syntax highlighting overlay
- Token chips: colored rounded badges with click handlers
- AST tree: nested divs with collapse/expand, indentation lines
- IR view: line-numbered pre block, diff coloring (green/red)
- Pass chips: draggable colored rectangles with `cursor: grab`
- Metrics panel: numbers with inline CSS bar widths
- Step indicators: horizontal tabs with active state

**JavaScript key sections:**
- `compile()`: POST to `/api/compile`, store response, render step 1
- `optimize(passOrder)`: POST to `/api/optimize`, render diff + metrics
- `runBenchmark()`: POST to `/api/benchmark`, render metrics table
- `renderTokens(tokens)`: build chip elements, wire click-to-highlight
- `renderAST(node, depth)`: recursive tree builder with collapse toggle
- `renderIR(instructions, text)`: line-numbered code block
- `renderDiff(diffLines)`: colored line display
- `renderMetrics(metrics)`: update numbers and bar widths
- Step navigation: `nextStep()`, `prevStep()`, show/hide sections
- Drag-and-drop: HTML5 drag events on pass chips, reorder array
- Mode toggle: show/hide learn vs explore panels
- `loadExample(name)`: GET `/api/examples/{name}`, populate editor
- Static explanatory content: object with paragraphs per phase

- [ ] **Step 2: Verify the page loads**

Run: `python -m compiler.web.app` (in background)
Open: `http://localhost:8080`
Expected: Dark-themed page loads with code editor and mode toggle.

- [ ] **Step 3: Test Learn Mode flow manually**

1. Paste `int main() { int x = 2 + 3; print(x); return 0; }`
2. Click "Compile"
3. Click "Next" through each step: Tokens, AST, Symbols, IR, Optimize, Execute
4. Verify each step renders correctly

- [ ] **Step 4: Test error handling**

1. Paste broken code: `int main( { }`
2. Click "Compile"
3. Verify error message appears with line/col highlighted

- [ ] **Step 5: Commit**

```bash
git add compiler/web/templates.py
git commit -m "feat: add complete frontend with Learn Mode step-through"
```

---

### Task 5: Build the Frontend — Explore Mode

**Files:**
- Modify: `compiler/web/templates.py`

- [ ] **Step 1: Add Explore Mode panels to the HTML**

Add the multi-panel layout to `INDEX_HTML`:
- Left panel: code editor (shared with Learn Mode)
- Center panel: IR view with unoptimized/optimized/diff toggle tabs
- Right panel: metrics dashboard with CSS bar charts
- Bottom toolbar: 6 draggable pass chips + "Apply" button + "Compare" button

- [ ] **Step 2: Implement drag-and-drop pass reordering**

JavaScript for HTML5 drag-and-drop:
- Each chip has `draggable="true"`, `ondragstart`, `ondragover`, `ondrop`
- Reordering updates a `passOrder` array
- "Apply" button calls `optimize(passOrder)` and re-renders center + right panels

- [ ] **Step 3: Implement Compare mode**

- "Compare" button pins current result as "A"
- Shows a preset dropdown (e.g., "CF->DCE->CSE->CP->SR->AS", "DCE->CF->CSE->CP->SR->AS", etc.)
- Selecting B runs a second optimize call
- Split-pane shows both IRs with metrics side-by-side
- "Exit Compare" returns to single view

- [ ] **Step 4: Test Explore Mode manually**

1. Switch to Explore mode
2. Load "factorial" example
3. Drag chips to reorder: CF, CP, DCE, CSE, SR, AS
4. Click Apply — verify IR updates, metrics update
5. Drag to different order — verify numbers change
6. Click Compare — verify split view works

- [ ] **Step 5: Test preloaded examples**

1. Click examples dropdown
2. Select each of the 8 programs
3. Verify each loads and compiles

- [ ] **Step 6: Commit**

```bash
git add compiler/web/templates.py
git commit -m "feat: add Explore Mode with drag-drop pass reordering and compare"
```

---

### Task 6: Polish and Final Integration

**Files:**
- Modify: `compiler/web/templates.py` (minor polish)
- Modify: `requirements.txt` (ensure complete)

- [ ] **Step 1: Add "How it works" explanatory content**

Add static paragraphs to the JavaScript in `templates.py`:

```javascript
const EXPLANATIONS = {
  lexer: "The lexer (tokenizer) reads source code character by character...",
  parser: "The parser checks that the token sequence follows grammar rules...",
  symbols: "The symbol table tracks every variable...",
  ir: "The IR generator translates the tree into flat instructions...",
  CF: "Constant Folding evaluates expressions with constant operands at compile time...",
  DCE: "Dead Code Elimination removes instructions that compute values never used...",
  CSE: "Common Subexpression Elimination detects repeated computations...",
  CP: "Copy Propagation replaces uses of a copied variable with the original...",
  SR: "Strength Reduction replaces expensive operations with cheaper equivalents...",
  AS: "Algebraic Simplification applies mathematical identities...",
};
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest -v`
Expected: All tests pass (test_compiler.py + test_web.py)

- [ ] **Step 3: Manual end-to-end test**

Run: `python -m compiler.web.app`

Test Learn Mode:
1. Load fibonacci example, step through all 7 stages
2. Verify token chips highlight source on click
3. Verify AST tree collapses/expands
4. Verify optimization diff shows red/green lines
5. Verify final execution shows correct output `[6765]`

Test Explore Mode:
1. Load factorial example
2. Reorder passes, verify metrics change
3. Compare two orderings side-by-side
4. Load all 8 examples, verify each works

Test error handling:
1. Type broken code, verify error appears with location

- [ ] **Step 4: Commit**

```bash
git add compiler/web/templates.py
git commit -m "feat: polish interactive learning tool with explanations and final testing"
```

- [ ] **Step 5: Verify existing CLI still works**

Run: `python -m compiler.main compiler/benchmarks/programs/factorial.c --optimize CF,DCE,CSE`
Expected: Same output as before — no regressions.
