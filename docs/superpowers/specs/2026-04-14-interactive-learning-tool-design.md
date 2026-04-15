# Interactive Compiler Learning Tool — Design Spec

## Overview

A browser-based interactive learning tool that wraps the existing compiler infrastructure, enabling university students and self-learners to visualize and experiment with every compiler phase — from lexing through optimization pass ordering. Served as a single Python process with no JS build step.

## Architecture

Single FastAPI process serving a self-contained HTML/CSS/JS frontend. No React, no npm, no external JS dependencies. Install is `pip install fastapi uvicorn`.

```
Browser (localhost:8080)
    |  REST API (JSON)
FastAPI server (compiler/web/app.py)
    |  imports directly
Existing compiler modules (unchanged*)
```

*One minor addition: `IRGenerator` gets a `generate_with_symbols()` method. This accumulates all declared symbols into a flat list during AST traversal (by appending to a list in `_gen_var_decl` and `_gen_function` param declarations) rather than reading from the scope stack at the end. The existing `generate()` method is unchanged.

### API Surface

| Method | Path | Request Body | Purpose |
|--------|------|-------------|---------|
| GET | `/` | — | Serves the single-page app |
| POST | `/api/compile` | `{"source": "int main() {...}"}` | Source -> tokens, AST, symbols, IR |
| POST | `/api/optimize` | `{"source": "...", "pass_order": ["CF","DCE"]}` | Compile + optimize -> diff, metrics, output |
| POST | `/api/benchmark` | `{"source": "..."}` | All 721 full orderings -> metrics array |
| GET | `/api/examples` | — | List program names from `compiler/benchmarks/programs/*.c` |
| GET | `/api/examples/{name}` | — | Get source code (name = filename stem, e.g. `fibonacci`) |

Note: `/api/benchmark` uses `all_full_orderings()` (721 permutations). On tested hardware completes in 5-15 seconds. Frontend shows a spinner.

No WebSocket — Learn Mode fetches all data from `/api/compile` at once, then the frontend steps through stages client-side.

### CORS

Same-origin only (frontend served by the same FastAPI process). No CORS middleware needed.

### Error Handling

All endpoints return structured errors for compiler failures:

```json
{
  "error": true,
  "phase": "parser",
  "message": "Expected RPAREN after if condition",
  "line": 3,
  "col": 12
}
```

- `LexerError`: `line` and `col` from the error.
- `ParseError`: extracted from `e.token.line` and `e.token.col`.
- `IRGeneratorError`: `line` and `col` are `null` (no source location available).

The frontend highlights the error location in the editor (when available) and shows the message. In Learn Mode, if parsing fails, the tool still shows the successful token stream, then displays the error at the parse step.

### API Response Schemas

**POST /api/compile response:**
```json
{
  "tokens": [{"type": "INT", "value": "int", "line": 1, "col": 1}, ...],
  "ast": {"type": "Program", "name": null, "line": 1, "col": 1, "fields": {"functions": [...]},
          "children": [
            {"type": "FunctionDecl", "name": "main", "line": 1, "col": 1,
             "fields": {"params": []},
             "children": [{"type": "Block", ...}]}
          ]},
  "symbols": [{"name": "x", "type": "int", "scope": 0, "ir_name": "x"}],
  "ir": [{"opcode": "LOAD_CONST", "dest": "t0", "src1": "5", "src2": null}, ...],
  "ir_text": "func main:\n  t0 = 5\n  ..."
}
```

**AST serialization:** Each node has `type` (class name), named `fields` (non-child scalar attributes like `name`, `op`, `value`), and `children` (a flat list of all child AST nodes in source order, regardless of their field name). The frontend tree renderer uses `type` for display and `children` for nesting. Named field semantics are not needed for the tree view.

**POST /api/optimize response:**
```json
{
  "pass_order": ["CF", "DCE"],
  "optimized_ir": [...],
  "optimized_ir_text": "...",
  "diff": [{"type": "kept", "text": "func main:"}, {"type": "removed", "text": "  t0 = 2"}, {"type": "added", "text": "  t0 = 5"}, ...],
  "metrics": {"code_size": 21, "estimated_cycles": 60.0, "dynamic_count": 53},
  "output": [120, 10, 10],
  "output_correct": true,
  "explanation": "Removed 5 instructions, added 1. Net reduction: 4 instructions."
}
```

### Pass Explanations (Dynamic)

For v1, the dynamic explanation is a **simple count-based summary**: "Removed N instructions, added M. Net reduction: K instructions." This is computed by diffing the before/after `ir_text` line counts by category (removed, added, kept). No semantic pattern matching — that is a future enhancement.

## Two Modes

### Learn Mode (Step-Through)

Linear walkthrough with "Next Step" / "Previous Step" buttons. The frontend fetches all data from `/api/compile` on initial compile, then steps through stages client-side.

Each step reveals one compiler phase:

1. **Source Code** — syntax-highlighted input editor
2. **Tokens** — colored chips showing token type and value. Click a token to highlight its source range (computed as `col` to `col + len(value)`).
3. **AST** — collapsible tree. Each node shows type, key fields, and `line:col`. Click a node to scroll the source editor to that line.
4. **Symbol Table** — table of variables, scopes, types.
5. **IR (Unoptimized)** — three-address code with line numbers.
6. **Optimization Step** — one pass at a time. Diff view uses **line-based text diff** on the `ir_text` strings. Added lines green, removed lines red. Static explanation paragraph plus count-based summary.
7. **Final IR + Execution** — interpreter output, dynamic instruction count, before/after metrics comparison.

### Explanatory Content

Each step has a collapsible "How it works" sidebar. Content is **static strings in `templates.py`** — one paragraph per phase:

- Lexer, Parser, Symbol Table, IR Generator: one paragraph each.
- Each of the 6 optimization passes: one paragraph each.
- Total: ~12 static paragraphs authored once.

### Explore Mode (Playground)

Multi-panel layout:

- **Left panel:** Code editor with examples dropdown.
- **Center panel:** IR view (toggle: unoptimized / optimized / diff).
- **Right panel:** Metrics dashboard (code size, cycles, dynamic count, CSS bar charts).
- **Bottom toolbar:** Drag-and-drop pass ordering chips. Reorder and hit "Apply".

**Compare feature:** Click "Compare" to pin current ordering as "A". Select a second ordering from a dropdown of common presets. Split-pane shows both IRs with metrics side-by-side. "Exit Compare" returns to single view.

## Frontend Design

Dark theme, code-editor aesthetic. Monospace for code/IR, sans-serif for UI. All vanilla HTML/CSS/JS in a single file (~1200 lines), no external dependencies.

### Key Components

- **Code Editor:** `<textarea>` with syntax highlighting overlay.
- **Token Chips:** Colored badges — blue (keywords), green (identifiers), orange (numbers), gray (operators).
- **AST Tree:** Nested collapsible `<div>`s with indentation lines. Click scrolls source to that line.
- **IR View:** Line-numbered code block. Diff: red (removed), green (added).
- **Pass Chips:** Draggable colored rectangles (CF, DCE, CSE, CP, SR, AS).
- **Metrics Panel:** Live numbers with CSS bar charts.
- **Example Dropdown:** All 8 benchmark programs from `compiler/benchmarks/programs/`.

## File Structure

New files:

```
compiler/web/
    __init__.py       # empty
    app.py            # FastAPI server, routes, serialization
    templates.py      # HTML/CSS/JS as Python string constant
    api_models.py     # Pydantic request/response models
```

One addition to existing code:
- `ir_generator.py`: add `generate_with_symbols()` that accumulates symbols during traversal into a flat list, returns `(instructions, symbols)`.

### Launch

```bash
python -m compiler.web.app
# Opens http://localhost:8080
```

### New Dependencies

```
fastapi>=0.100
uvicorn>=0.20
```

## Scope Exclusions

- No user accounts, persistence, or database.
- No multi-user / shared sessions.
- No mobile-responsive layout (desktop-first).
- No external CDN dependencies — fully offline-capable.
- No AST end-position tracking (click-to-line only, not range highlighting).
- No semantic pattern-matching in pass explanations (v1 uses count-based summaries).

## Success Criteria

1. Student pastes code, clicks "Next", and sees every compiler phase unfold with explanations.
2. Student drags pass chips into a new order, hits Apply, and sees the IR change instantly with updated metrics.
3. Compilation errors show the error location highlighted in the editor with a message.
4. The tool runs with `pip install` + one command. No Node.js, no build step.
5. All 8 benchmark programs are preloaded and explorable.
