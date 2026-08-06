"""
RISC-V RV32IM Assembly Backend.

Translates optimized Three-Address Code into GNU-syntax RV32IM assembly
targeting Linux user mode (runnable under `qemu-riscv32` after assembling
with a RISC-V GCC, e.g.:

    riscv64-linux-gnu-gcc -march=rv32im -mabi=ilp32 -static -nostdlib \
        -o prog prog.s
    qemu-riscv32 ./prog

Code generation strategy (classic course-compiler approach):
  - Every IR variable, temporary, and array gets a stack slot in its
    function's frame; values are loaded into t0/t1, computed into t2,
    and stored back. No register allocation — the point of this
    backend is faithful, readable lowering, not peak performance.
  - Globals live in .data and are accessed via la/lw/sw, matching the
    GLOBAL_LOAD/GLOBAL_STORE opcodes.
  - print(x) calls a built-in print_int routine (decimal + newline via
    the Linux write syscall); the program exits through the exit
    syscall with main's return value as the status code.

Semantics notes:
  - Division/modulo by zero yields 0, matching the IR interpreter, via
    an explicit guard branch (hardware div would give -1/-dividend).
  - Array accesses are not bounds-checked (the interpreter clamps
    out-of-range accesses; benchmark programs are in-bounds).
  - Arithmetic wraps at 32 bits, whereas the interpreter uses Python
    unbounded integers; programs staying within int32 behave identically.
"""

from __future__ import annotations

from compiler.errors import CompilerError
from compiler.ir import IRInstruction, IROpcode, is_constant


class CodegenError(CompilerError):
    pass


# Maximum immediate magnitude usable directly in addi/lw/sw offsets.
_IMM_LIMIT = 2040

_ARG_REGS = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]

_BINARY_ASM = {
    IROpcode.ADD: "add",
    IROpcode.SUB: "sub",
    IROpcode.MUL: "mul",
}


class RiscvCodeGenerator:
    """Emits RV32IM assembly from a flat IR instruction list."""

    def __init__(self, instructions: list[IRInstruction]):
        self._instructions = instructions
        self._lines: list[str] = []
        self._globals: list[tuple[str, str]] = []   # (name, init)
        self._offsets: dict[str, int] = {}          # var -> offset from s0
        self._array_offsets: dict[str, tuple[int, int]] = {}  # name -> (offset, size)
        self._frame_size = 0
        self._func_name = ""
        self._unique = 0
        self._param_queue: list[str] = []
        # ir instruction index -> (first asm line, one-past-last asm line)
        self._inst_ranges: dict[int, tuple[int, int]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self) -> str:
        """Generate the full assembly module."""
        self._lines = []
        self._globals = [
            (inst.dest, inst.src1 or "0")
            for inst in self._instructions
            if inst.opcode == IROpcode.GLOBAL_DECL and inst.dest
        ]

        self._emit_header()

        i = 0
        n = len(self._instructions)
        while i < n:
            inst = self._instructions[i]
            if inst.opcode == IROpcode.FUNC_BEGIN:
                end = self._find_func_end(i)
                self._gen_function(self._instructions[i:end + 1], base_index=i)
                i = end + 1
            else:
                i += 1  # top-level GLOBAL_DECLs already collected

        self._emit_runtime()
        self._emit_data()
        return "\n".join(self._lines) + "\n"

    def generate_with_mapping(self) -> tuple[str, dict[int, tuple[int, int]]]:
        """Generate assembly plus an IR-index -> asm-line-range mapping.

        Line numbers are 0-based indices into the returned text's lines.
        Only instruction indices that produced assembly appear as keys.
        """
        asm = self.generate()
        return asm, dict(self._inst_ranges)

    # ------------------------------------------------------------------
    # Module structure
    # ------------------------------------------------------------------

    def _emit(self, text: str) -> None:
        self._lines.append(text)

    def _emit_header(self) -> None:
        self._emit("    .text")
        self._emit("    .globl _start")
        self._emit("_start:")
        self._emit("    call main")
        self._emit("    li a7, 93              # exit syscall")
        self._emit("    ecall")
        self._emit("")

    def _emit_data(self) -> None:
        if not self._globals:
            return
        self._emit("")
        self._emit("    .data")
        for name, init in self._globals:
            self._emit(f"{name}: .word {init}")

    def _find_func_end(self, start: int) -> int:
        for j in range(start + 1, len(self._instructions)):
            if self._instructions[j].opcode == IROpcode.FUNC_END:
                return j
        raise CodegenError(
            f"FUNC_BEGIN '{self._instructions[start].dest}' has no FUNC_END"
        )

    # ------------------------------------------------------------------
    # Frame layout
    # ------------------------------------------------------------------

    def _assign_slots(self, body: list[IRInstruction]) -> None:
        """Assign a stack slot to every variable and array in the function."""
        self._offsets = {}
        self._array_offsets = {}
        global_names = {name for name, _ in self._globals}

        names: list[str] = []
        arrays: list[tuple[str, int]] = []
        seen: set[str] = set()

        def add(name: str | None) -> None:
            if name and name not in seen and name not in global_names \
                    and not is_constant(name):
                seen.add(name)
                names.append(name)

        for inst in body:
            if inst.opcode == IROpcode.ARR_DECL and inst.dest:
                if inst.dest not in seen:
                    seen.add(inst.dest)
                    arrays.append((inst.dest, int(inst.src1 or "0")))
                continue
            if inst.opcode in (IROpcode.ARR_LOAD,):
                add(inst.dest)
                add(inst.src2)
                continue
            if inst.opcode == IROpcode.ARR_STORE:
                add(inst.src1)
                add(inst.src2)
                continue
            if inst.opcode == IROpcode.GLOBAL_LOAD:
                add(inst.dest)
                continue
            if inst.opcode == IROpcode.GLOBAL_STORE:
                add(inst.src1)
                continue
            add(inst.defined_var())
            for used in inst.used_vars():
                add(used)
            if inst.opcode == IROpcode.FUNC_PARAM:
                add(inst.dest)

        # Layout below the saved ra/s0 pair: ra at -4(s0), s0 at -8(s0).
        offset = -8
        for name in names:
            offset -= 4
            self._offsets[name] = offset
        for name, size in arrays:
            offset -= 4 * max(size, 1)
            self._array_offsets[name] = (offset, size)

        raw = -offset
        self._frame_size = (raw + 15) // 16 * 16  # 16-byte aligned

    # ------------------------------------------------------------------
    # Value movement helpers
    # ------------------------------------------------------------------

    def _slot(self, name: str) -> int:
        if name not in self._offsets:
            raise CodegenError(
                f"No stack slot for '{name}' in function '{self._func_name}'"
            )
        return self._offsets[name]

    def _load(self, reg: str, operand: str) -> None:
        """Load a constant or variable value into a register."""
        if is_constant(operand):
            self._emit(f"    li {reg}, {operand}")
            return
        off = self._slot(operand)
        if abs(off) <= _IMM_LIMIT:
            self._emit(f"    lw {reg}, {off}(s0)")
        else:
            self._emit(f"    li t6, {off}")
            self._emit("    add t6, s0, t6")
            self._emit(f"    lw {reg}, 0(t6)")

    def _store(self, reg: str, name: str) -> None:
        """Store a register into a variable's stack slot."""
        off = self._slot(name)
        if abs(off) <= _IMM_LIMIT:
            self._emit(f"    sw {reg}, {off}(s0)")
        else:
            self._emit(f"    li t6, {off}")
            self._emit("    add t6, s0, t6")
            self._emit(f"    sw {reg}, 0(t6)")

    def _array_base(self, reg: str, name: str) -> None:
        """Load an array's base address into a register."""
        if name not in self._array_offsets:
            raise CodegenError(
                f"Unknown array '{name}' in function '{self._func_name}'"
            )
        off, _ = self._array_offsets[name]
        if abs(off) <= _IMM_LIMIT:
            self._emit(f"    addi {reg}, s0, {off}")
        else:
            self._emit(f"    li {reg}, {off}")
            self._emit(f"    add {reg}, s0, {reg}")

    def _label(self, stem: str) -> str:
        self._unique += 1
        return f".L{stem}_{self._unique}"

    # ------------------------------------------------------------------
    # Function code generation
    # ------------------------------------------------------------------

    def _gen_function(self, body: list[IRInstruction], base_index: int = 0) -> None:
        func = body[0].dest or "anon"
        self._func_name = func
        self._param_queue = []
        self._assign_slots(body)

        frame = self._frame_size + 16  # room for saved ra/s0 + padding
        prologue_start = len(self._lines)
        self._emit(f"{func}:")
        self._emit(f"    addi sp, sp, -{frame}")
        self._emit(f"    sw ra, {frame - 4}(sp)")
        self._emit(f"    sw s0, {frame - 8}(sp)")
        self._emit(f"    addi s0, sp, {frame}")

        # Bind incoming arguments (FUNC_PARAM instructions follow FUNC_BEGIN)
        param_idx = 0
        for offset, inst in enumerate(body[1:], start=1):
            if inst.opcode != IROpcode.FUNC_PARAM:
                break
            if param_idx >= len(_ARG_REGS):
                raise CodegenError(
                    f"Function '{func}' has more than {len(_ARG_REGS)} parameters"
                )
            start = len(self._lines)
            self._store(_ARG_REGS[param_idx], inst.dest)
            self._inst_ranges[base_index + offset] = (start, len(self._lines))
            param_idx += 1
        self._inst_ranges[base_index] = (prologue_start, prologue_start + 5)

        ret_label = f".Lret_{func}"
        for offset, inst in enumerate(body[1:-1], start=1):
            if inst.opcode == IROpcode.FUNC_PARAM:
                continue  # already emitted with the prologue
            start = len(self._lines)
            self._gen_instruction(inst, ret_label)
            if len(self._lines) > start:
                self._inst_ranges[base_index + offset] = (start, len(self._lines))

        # Fall-through return value is 0, matching the interpreter
        epilogue_start = len(self._lines)
        self._emit("    li a0, 0")
        self._emit(f"{ret_label}:")
        self._emit(f"    lw ra, {frame - 4}(sp)")
        self._emit(f"    lw s0, {frame - 8}(sp)")
        self._emit(f"    addi sp, sp, {frame}")
        self._emit("    ret")
        self._inst_ranges[base_index + len(body) - 1] = (
            epilogue_start, len(self._lines),
        )
        self._emit("")

    def _gen_instruction(self, inst: IRInstruction, ret_label: str) -> None:
        op = inst.opcode

        if op in (IROpcode.NOP, IROpcode.FUNC_PARAM, IROpcode.GLOBAL_DECL):
            return

        if op == IROpcode.LABEL:
            self._emit(f"{inst.dest}:")
            return

        if op == IROpcode.JUMP:
            self._emit(f"    j {inst.dest}")
            return

        if op == IROpcode.JUMP_IF_TRUE:
            self._load("t0", inst.src1)
            self._emit(f"    bnez t0, {inst.dest}")
            return

        if op == IROpcode.JUMP_IF_FALSE:
            self._load("t0", inst.src1)
            self._emit(f"    beqz t0, {inst.dest}")
            return

        if op in (IROpcode.LOAD_CONST, IROpcode.COPY):
            self._load("t0", inst.src1)
            self._store("t0", inst.dest)
            return

        if op in _BINARY_ASM:
            self._load("t0", inst.src1)
            self._load("t1", inst.src2)
            self._emit(f"    {_BINARY_ASM[op]} t2, t0, t1")
            self._store("t2", inst.dest)
            return

        if op in (IROpcode.DIV, IROpcode.MOD):
            mnemonic = "div" if op == IROpcode.DIV else "rem"
            zero_l = self._label("divz")
            done_l = self._label("divdone")
            self._load("t0", inst.src1)
            self._load("t1", inst.src2)
            self._emit(f"    beqz t1, {zero_l}")
            self._emit(f"    {mnemonic} t2, t0, t1")
            self._emit(f"    j {done_l}")
            self._emit(f"{zero_l}:")
            self._emit("    li t2, 0               # x/0 == 0 by language rule")
            self._emit(f"{done_l}:")
            self._store("t2", inst.dest)
            return

        if op == IROpcode.NEG:
            self._load("t0", inst.src1)
            self._emit("    neg t2, t0")
            self._store("t2", inst.dest)
            return

        if op == IROpcode.NOT:
            self._load("t0", inst.src1)
            self._emit("    seqz t2, t0")
            self._store("t2", inst.dest)
            return

        if op in (IROpcode.EQ, IROpcode.NEQ, IROpcode.LT, IROpcode.GT,
                  IROpcode.LTE, IROpcode.GTE, IROpcode.AND, IROpcode.OR):
            self._load("t0", inst.src1)
            self._load("t1", inst.src2)
            self._gen_comparison(op)
            self._store("t2", inst.dest)
            return

        if op == IROpcode.PARAM:
            self._param_queue.append(inst.src1 or "0")
            return

        if op == IROpcode.CALL:
            if len(self._param_queue) > len(_ARG_REGS):
                raise CodegenError(
                    f"Call to '{inst.src1}' passes more than "
                    f"{len(_ARG_REGS)} arguments"
                )
            for idx, operand in enumerate(self._param_queue):
                self._load(_ARG_REGS[idx], operand)
            self._param_queue = []
            self._emit(f"    call {inst.src1}")
            self._store("a0", inst.dest)
            return

        if op == IROpcode.RETURN:
            if inst.src1:
                self._load("a0", inst.src1)
            else:
                self._emit("    li a0, 0")
            self._emit(f"    j {ret_label}")
            return

        if op == IROpcode.PRINT:
            self._load("a0", inst.src1)
            self._emit("    call print_int")
            return

        if op == IROpcode.ARR_DECL:
            size = int(inst.src1 or "0")
            if size <= 0:
                return
            loop_l = self._label("zeroinit")
            self._array_base("t0", inst.dest)
            self._emit(f"    li t1, {size}")
            self._emit(f"{loop_l}:")
            self._emit("    sw zero, 0(t0)")
            self._emit("    addi t0, t0, 4")
            self._emit("    addi t1, t1, -1")
            self._emit(f"    bnez t1, {loop_l}")
            return

        if op == IROpcode.ARR_LOAD:
            self._load("t0", inst.src2)          # index
            self._emit("    slli t0, t0, 2")
            self._array_base("t1", inst.src1)
            self._emit("    add t1, t1, t0")
            self._emit("    lw t2, 0(t1)")
            self._store("t2", inst.dest)
            return

        if op == IROpcode.ARR_STORE:
            self._load("t0", inst.src1)          # index
            self._emit("    slli t0, t0, 2")
            self._array_base("t1", inst.dest)
            self._emit("    add t1, t1, t0")
            self._load("t2", inst.src2)          # value
            self._emit("    sw t2, 0(t1)")
            return

        if op == IROpcode.GLOBAL_LOAD:
            self._emit(f"    la t0, {inst.src1}")
            self._emit("    lw t1, 0(t0)")
            self._store("t1", inst.dest)
            return

        if op == IROpcode.GLOBAL_STORE:
            self._load("t0", inst.src1)
            self._emit(f"    la t1, {inst.dest}")
            self._emit("    sw t0, 0(t1)")
            return

        raise CodegenError(f"Unsupported IR opcode: {op.name}")

    def _gen_comparison(self, op: IROpcode) -> None:
        """Emit t2 = t0 <op> t1 for comparison/logical opcodes (0/1 result)."""
        if op == IROpcode.EQ:
            self._emit("    sub t2, t0, t1")
            self._emit("    seqz t2, t2")
        elif op == IROpcode.NEQ:
            self._emit("    sub t2, t0, t1")
            self._emit("    snez t2, t2")
        elif op == IROpcode.LT:
            self._emit("    slt t2, t0, t1")
        elif op == IROpcode.GT:
            self._emit("    slt t2, t1, t0")
        elif op == IROpcode.LTE:
            self._emit("    slt t2, t1, t0")
            self._emit("    xori t2, t2, 1")
        elif op == IROpcode.GTE:
            self._emit("    slt t2, t0, t1")
            self._emit("    xori t2, t2, 1")
        elif op == IROpcode.AND:
            self._emit("    snez t0, t0")
            self._emit("    snez t1, t1")
            self._emit("    and t2, t0, t1")
        elif op == IROpcode.OR:
            self._emit("    or t2, t0, t1")
            self._emit("    snez t2, t2")

    # ------------------------------------------------------------------
    # Runtime support
    # ------------------------------------------------------------------

    def _emit_runtime(self) -> None:
        """print_int: write a0 as decimal + newline to stdout."""
        self._emit("print_int:")
        self._emit("    addi sp, sp, -48")
        self._emit("    sw ra, 44(sp)")
        self._emit("    mv t0, a0")
        self._emit("    li t2, 10")
        self._emit("    addi t1, sp, 31        # digits filled backwards")
        self._emit("    li t3, 10              # '\\n'")
        self._emit("    sb t3, 0(t1)")
        self._emit("    slti t4, t0, 0         # remember sign")
        self._emit("    beqz t4, .Lpi_digits")
        self._emit("    neg t0, t0")
        self._emit(".Lpi_digits:")
        self._emit("    rem t5, t0, t2")
        self._emit("    addi t5, t5, 48        # '0' + digit")
        self._emit("    addi t1, t1, -1")
        self._emit("    sb t5, 0(t1)")
        self._emit("    div t0, t0, t2")
        self._emit("    bnez t0, .Lpi_digits")
        self._emit("    beqz t4, .Lpi_write")
        self._emit("    addi t1, t1, -1")
        self._emit("    li t5, 45              # '-'")
        self._emit("    sb t5, 0(t1)")
        self._emit(".Lpi_write:")
        self._emit("    addi t5, sp, 32")
        self._emit("    sub a2, t5, t1         # length")
        self._emit("    mv a1, t1              # buffer")
        self._emit("    li a0, 1               # stdout")
        self._emit("    li a7, 64              # write syscall")
        self._emit("    ecall")
        self._emit("    lw ra, 44(sp)")
        self._emit("    addi sp, sp, 48")
        self._emit("    ret")


def generate_riscv(instructions: list[IRInstruction]) -> str:
    """Convenience: emit RV32IM assembly for an IR program."""
    return RiscvCodeGenerator(instructions).generate()
