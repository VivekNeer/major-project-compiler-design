"""FastAPI web server for the interactive compiler learning tool."""
from __future__ import annotations
import difflib
import glob
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParseError
from compiler.ir_generator import IRGenerator, IRGeneratorError
from compiler.symbol_table import SymbolTableError
from compiler.semantic_analyzer import check_semantics, SemanticError
from compiler.ir import format_ir
from compiler.interpreter import execute_ir, InterpreterError
from compiler.optimizations.pass_manager import PassManager
from compiler.codegen_riscv import (
    generate_riscv, RiscvCodeGenerator, CodegenError,
)
from compiler.benchmarks.metric_collector import count_code_size, estimate_cycles
from compiler.web.api_models import (
    CompileRequest, OptimizeRequest, BenchmarkRequest,
    OptimizeStepsRequest, AssemblyRequest,
)
from compiler.web.templates import INDEX_HTML
from compiler.ast_nodes import ASTNode

app = FastAPI(title="Compiler Explorer")

PROGRAMS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "benchmarks", "programs")
)
EXAMPLE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


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


def _error_phase(e: Exception) -> str:
    """Map exceptions to stable API phase names."""
    if isinstance(e, LexerError):
        return "lexer"
    if isinstance(e, ParseError):
        return "parser"
    if isinstance(e, SemanticError):
        return "semantic"
    if isinstance(e, (IRGeneratorError, SymbolTableError)):
        return "ir_generator"
    if isinstance(e, ValueError):
        return "optimization"
    return "runtime"


def get_example_description(source: str) -> str:
    """Extract first comment line as description."""
    doc, _ = extract_doc_comment(source)
    if doc:
        return doc["title"]
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            return stripped.lstrip("/ ").rstrip(".")
    return ""


def get_example_suite(source: str) -> str:
    """Classify an example by which benchmark suite its doc comment cites."""
    if "PolyBench" in source:
        return "PolyBench"
    if "MiBench" in source:
        return "MiBench"
    return "Other"


def extract_doc_comment(source: str) -> tuple[dict | None, str]:
    """Split a leading /* ... */ doc comment into a structured heading
    ("title" + bullet "points") and return it alongside the source with
    that comment (and the blank line after it) removed.
    """
    stripped = source.lstrip("\n")
    if not stripped.startswith("/*"):
        return None, source
    end = stripped.find("*/")
    if end == -1:
        return None, source

    lines = []
    for raw_line in stripped[2:end].splitlines():
        line = raw_line.strip()
        if line.startswith("*"):
            line = line[1:].strip()
        if line:
            lines.append(line)

    remaining_source = stripped[end + 2:].lstrip("\n")
    if not lines:
        return None, remaining_source

    title = lines[0].rstrip(".")
    body = " ".join(lines[1:])
    points = []
    for sentence in body.split(". "):
        sentence = sentence.strip()
        if not sentence:
            continue
        if not sentence.endswith((".", ":")):
            sentence += "."
        points.append(sentence)

    return {"title": title, "points": points}, remaining_source


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the built React app when present, else the legacy page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return INDEX_HTML


@app.get("/legacy", response_class=HTMLResponse)
def legacy_index():
    return INDEX_HTML


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    from fastapi.responses import FileResponse
    path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/svg+xml")
    raise HTTPException(status_code=404)


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

    # Semantic analysis
    try:
        check_semantics(ast)
    except SemanticError as e:
        return make_error("semantic", e)

    # Generate IR + symbols
    try:
        gen = IRGenerator()
        ir, symbols = gen.generate_with_symbols(ast)
    except (IRGeneratorError, SymbolTableError) as e:
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
        check_semantics(ast)
        base_ir = IRGenerator().generate(ast)
        pm = PassManager(req.pass_order)
        opt_ir = pm.run(base_ir)
    except (LexerError, ParseError, IRGeneratorError, SymbolTableError, SemanticError, ValueError) as e:
        return make_error(_error_phase(e), e)

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

    try:
        assembly = generate_riscv(opt_ir)
    except CodegenError as e:
        assembly = f"# codegen error: {e}"

    return {
        "pass_order": req.pass_order,
        "optimized_ir": serialize_ir(opt_ir),
        "optimized_ir_text": opt_text,
        "assembly": assembly,
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
        check_semantics(ast)
        base_ir = IRGenerator().generate(ast)
    except (LexerError, ParseError, IRGeneratorError, SymbolTableError, SemanticError) as e:
        return make_error(_error_phase(e), e)

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


@app.post("/api/optimize-steps")
def optimize_steps(req: OptimizeStepsRequest):
    """Apply the ordering one pass at a time, returning every stage."""
    try:
        tokens = Lexer(req.source).tokenize()
        ast = Parser(tokens).parse()
        check_semantics(ast)
        ir = IRGenerator().generate(ast)
        PassManager(req.pass_order)  # validate names before stepping
    except (LexerError, ParseError, IRGeneratorError, SymbolTableError,
            SemanticError, ValueError) as e:
        return make_error(_error_phase(e), e)

    try:
        base_exec = execute_ir(ir)
        base_output = base_exec.output
    except (InterpreterError, RecursionError):
        base_output = None

    stages = [{
        "pass": None,
        "label": "Baseline",
        "ir_text": format_ir(ir),
        "diff": [],
        "code_size": count_code_size(ir),
        "estimated_cycles": estimate_cycles(ir),
        "removed": 0,
        "added": 0,
    }]

    current = ir
    for name in req.pass_order:
        nxt = PassManager([name]).run(current)
        diff = compute_diff(format_ir(current), format_ir(nxt))
        stages.append({
            "pass": name,
            "label": name,
            "ir_text": format_ir(nxt),
            "diff": diff,
            "code_size": count_code_size(nxt),
            "estimated_cycles": estimate_cycles(nxt),
            "removed": sum(1 for d in diff if d["type"] == "removed"),
            "added": sum(1 for d in diff if d["type"] == "added"),
        })
        current = nxt

    correct = None
    if base_output is not None:
        try:
            correct = execute_ir(current).output == base_output
        except (InterpreterError, RecursionError):
            correct = False

    return {
        "pass_order": req.pass_order,
        "stages": stages,
        "output_correct": correct,
    }


@app.post("/api/assembly")
def assembly(req: AssemblyRequest):
    """Emit RISC-V assembly with an IR-line <-> asm-line mapping."""
    try:
        tokens = Lexer(req.source).tokenize()
        ast = Parser(tokens).parse()
        check_semantics(ast)
        ir = IRGenerator().generate(ast)
        if req.pass_order:
            ir = PassManager(req.pass_order).run(ir)
        asm, inst_ranges = RiscvCodeGenerator(ir).generate_with_mapping()
    except (LexerError, ParseError, IRGeneratorError, SymbolTableError,
            SemanticError, CodegenError, ValueError) as e:
        return make_error(_error_phase(e), e)

    # format_ir skips NOPs, so rebuild the shown-line <-> instruction
    # index correspondence here.
    ir_lines: list[str] = []
    mapping: list[dict] = []
    from compiler.ir import format_instruction, IROpcode
    for idx, inst in enumerate(ir):
        if inst.opcode == IROpcode.NOP:
            continue
        line_no = len(ir_lines)
        ir_lines.append(format_instruction(inst))
        if idx in inst_ranges:
            lo, hi = inst_ranges[idx]
            mapping.append({"ir_line": line_no, "asm_start": lo, "asm_end": hi})

    return {
        "pass_order": req.pass_order,
        "ir_lines": ir_lines,
        "asm_lines": asm.splitlines(),
        "mapping": mapping,
    }


@app.get("/api/examples")
def list_examples():
    files = sorted(glob.glob(os.path.join(PROGRAMS_DIR, "*.c")))
    examples = []
    for filepath in files:
        name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r") as f:
            source = f.read()
        examples.append({
            "name": name,
            "description": get_example_description(source),
            "suite": get_example_suite(source),
        })
    return examples


@app.get("/api/examples/{name}")
def get_example(name: str):
    if not EXAMPLE_NAME_RE.fullmatch(name):
        raise HTTPException(status_code=404, detail=f"Example '{name}' not found")

    filepath = os.path.abspath(os.path.join(PROGRAMS_DIR, f"{name}.c"))
    if os.path.commonpath([PROGRAMS_DIR, filepath]) != PROGRAMS_DIR:
        raise HTTPException(status_code=404, detail=f"Example '{name}' not found")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Example '{name}' not found")
    with open(filepath, "r") as f:
        source = f.read()
    doc, code = extract_doc_comment(source)
    return {"name": name, "source": code, "doc": doc}


# Mount built frontend assets (present after `npm run build` in frontend/)
if os.path.isdir(os.path.join(STATIC_DIR, "assets")):
    from fastapi.staticfiles import StaticFiles
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
        name="assets",
    )


if __name__ == "__main__":
    import uvicorn
    print("Starting Compiler Explorer at http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
