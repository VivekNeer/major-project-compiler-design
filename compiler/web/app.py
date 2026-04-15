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
from compiler.ir import format_ir, IROpcode
from compiler.interpreter import execute_ir, InterpreterError
from compiler.optimizations.pass_manager import PassManager, PASS_NAMES
from compiler.benchmarks.metric_collector import count_code_size, estimate_cycles
from compiler.web.api_models import CompileRequest, OptimizeRequest, BenchmarkRequest
from compiler.web.templates import INDEX_HTML
from compiler.ast_nodes import ASTNode

app = FastAPI(title="Compiler Explorer")

PROGRAMS_DIR = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "programs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def serialize_ast(node: ASTNode) -> dict:
    """Recursively serialize an AST node to a JSON-compatible dict."""
    result: dict = {
        "type": type(node).__name__,
        "line": getattr(node, "line", 0),
        "col": getattr(node, "col", 0),
        "fields": {},
        "children": [],
    }
    for key, val in node.__dict__.items():
        if key in ("line", "col"):
            continue
        if isinstance(val, ASTNode):
            result["children"].append(serialize_ast(val))
        elif isinstance(val, list):
            has_ast = False
            for item in val:
                if isinstance(item, ASTNode):
                    result["children"].append(serialize_ast(item))
                    has_ast = True
            if not has_ast:
                result["fields"][key] = val
        else:
            result["fields"][key] = val
    return result


def serialize_ir(instructions) -> list[dict]:
    """Serialize IR instructions to JSON-compatible dicts."""
    return [
        {"opcode": i.opcode.name, "dest": i.dest, "src1": i.src1, "src2": i.src2}
        for i in instructions
    ]


def compute_diff(before_text: str, after_text: str) -> list[dict]:
    """Line-based diff of IR text."""
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()
    result = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, before_lines, after_lines
    ).get_opcodes():
        if tag == "equal":
            for line in before_lines[i1:i2]:
                result.append({"type": "kept", "text": line})
        elif tag == "delete":
            for line in before_lines[i1:i2]:
                result.append({"type": "removed", "text": line})
        elif tag == "insert":
            for line in after_lines[j1:j2]:
                result.append({"type": "added", "text": line})
        elif tag == "replace":
            for line in before_lines[i1:i2]:
                result.append({"type": "removed", "text": line})
            for line in after_lines[j1:j2]:
                result.append({"type": "added", "text": line})
    return result


def make_error(phase: str, e: Exception) -> dict:
    """Build a structured error response."""
    line = getattr(e, "line", None)
    col = getattr(e, "col", None)
    if line is None and hasattr(e, "token"):
        line = getattr(e.token, "line", None)
        col = getattr(e.token, "col", None)
    return {"error": True, "phase": phase, "message": str(e), "line": line, "col": col}


def get_example_description(source: str) -> str:
    """Extract first comment line as description."""
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("/*"):
            return stripped.lstrip("/* ").rstrip(" */").rstrip(".")
        if stripped.startswith("//"):
            return stripped.lstrip("/ ").rstrip(".")
    return ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.post("/api/compile")
def compile_source(req: CompileRequest):
    # Lex
    try:
        tokens = Lexer(req.source).tokenize()
    except LexerError as e:
        return make_error("lexer", e)

    # Parse
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        return make_error("parser", e)

    # Generate IR + symbols
    try:
        gen = IRGenerator()
        ir, symbols = gen.generate_with_symbols(ast)
    except IRGeneratorError as e:
        return make_error("ir_generator", e)

    return {
        "tokens": [
            {"type": t.type.name, "value": t.value, "line": t.line, "col": t.col}
            for t in tokens if t.type.name != "EOF"
        ],
        "ast": serialize_ast(ast),
        "symbols": symbols,
        "ir": serialize_ir(ir),
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
        return make_error(phase, e)

    base_text = format_ir(base_ir)
    opt_text = format_ir(opt_ir)
    diff = compute_diff(base_text, opt_text)

    removed = sum(1 for d in diff if d["type"] == "removed")
    added = sum(1 for d in diff if d["type"] == "added")
    net = removed - added
    explanation = f"Removed {removed} instructions, added {added}. Net reduction: {net}."

    # Dynamic execution
    try:
        base_exec = execute_ir(base_ir)
        opt_exec = execute_ir(opt_ir)
        dyn_count = opt_exec.dynamic_instruction_count
        output = opt_exec.output
        correct = base_exec.output == opt_exec.output
    except (InterpreterError, RecursionError):
        dyn_count = 0
        output = []
        correct = False

    return {
        "pass_order": req.pass_order,
        "optimized_ir": serialize_ir(opt_ir),
        "optimized_ir_text": opt_text,
        "diff": diff,
        "metrics": {
            "code_size": count_code_size(opt_ir),
            "estimated_cycles": estimate_cycles(opt_ir),
            "dynamic_count": dyn_count,
        },
        "output": output,
        "output_correct": correct,
        "explanation": explanation,
    }


@app.post("/api/benchmark")
def benchmark(req: BenchmarkRequest):
    try:
        tokens = Lexer(req.source).tokenize()
        ast = Parser(tokens).parse()
        base_ir = IRGenerator().generate(ast)
    except (LexerError, ParseError, IRGeneratorError) as e:
        phase = type(e).__name__.replace("Error", "").lower()
        return make_error(phase, e)

    base_exec = execute_ir(base_ir)
    orderings = PassManager.all_full_orderings()
    results = []

    for ordering in orderings:
        pm = PassManager(ordering)
        opt_ir = pm.run(base_ir)
        label = " -> ".join(ordering) if ordering else "Baseline (none)"

        try:
            opt_exec = execute_ir(opt_ir)
            dyn_count = opt_exec.dynamic_instruction_count
            correct = base_exec.output == opt_exec.output
        except (InterpreterError, RecursionError):
            dyn_count = 0
            correct = False

        entry = {
            "pass_order": ordering,
            "label": label,
            "code_size": count_code_size(opt_ir),
            "estimated_cycles": estimate_cycles(opt_ir),
            "dynamic_count": dyn_count,
            "output_correct": correct,
        }
        results.append(entry)

    baseline = next((r for r in results if not r["pass_order"]), results[0])
    return {"results": results, "baseline": baseline}


@app.get("/api/examples")
def list_examples():
    files = sorted(glob.glob(os.path.join(PROGRAMS_DIR, "*.c")))
    examples = []
    for filepath in files:
        name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r") as f:
            source = f.read()
        examples.append({"name": name, "description": get_example_description(source)})
    return examples


@app.get("/api/examples/{name}")
def get_example(name: str):
    filepath = os.path.join(PROGRAMS_DIR, f"{name}.c")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Example '{name}' not found")
    with open(filepath, "r") as f:
        source = f.read()
    return {"name": name, "source": source}


if __name__ == "__main__":
    import uvicorn
    print("Starting Compiler Explorer at http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
