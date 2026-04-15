"""
Intermediate Representation (IR) — Three-Address Code (3AC).

Each instruction has at most one operator and up to two source operands,
producing one result.  This flat representation is easy to analyse and
reorder during optimization passes.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class IROpcode(Enum):
    # Arithmetic / logic
    ADD = auto()        # dest = src1 + src2
    SUB = auto()        # dest = src1 - src2
    MUL = auto()        # dest = src1 * src2
    DIV = auto()        # dest = src1 / src2
    MOD = auto()        # dest = src1 % src2
    NEG = auto()        # dest = -src1

    # Comparison (result is 0 or 1)
    EQ = auto()         # dest = src1 == src2
    NEQ = auto()        # dest = src1 != src2
    LT = auto()         # dest = src1 <  src2
    GT = auto()         # dest = src1 >  src2
    LTE = auto()        # dest = src1 <= src2
    GTE = auto()        # dest = src1 >= src2

    # Logical
    AND = auto()        # dest = src1 && src2
    OR = auto()         # dest = src1 || src2
    NOT = auto()        # dest = !src1

    # Data movement
    COPY = auto()       # dest = src1
    LOAD_CONST = auto() # dest = <immediate integer>

    # Control flow
    LABEL = auto()      # label:
    JUMP = auto()        # goto label
    JUMP_IF_TRUE = auto()   # if src1 goto label
    JUMP_IF_FALSE = auto()  # iffalse src1 goto label

    # Functions
    PARAM = auto()      # param src1
    CALL = auto()       # dest = call func, nargs
    RETURN = auto()     # return src1
    FUNC_BEGIN = auto() # function entry marker
    FUNC_END = auto()   # function exit marker
    FUNC_PARAM = auto() # parameter declaration: dest = nth parameter

    # I/O
    PRINT = auto()      # print src1

    # No-op (placeholder for eliminated instructions)
    NOP = auto()


# Map source-level operators to IR opcodes
OP_TO_OPCODE = {
    "+": IROpcode.ADD,
    "-": IROpcode.SUB,
    "*": IROpcode.MUL,
    "/": IROpcode.DIV,
    "%": IROpcode.MOD,
    "==": IROpcode.EQ,
    "!=": IROpcode.NEQ,
    "<": IROpcode.LT,
    ">": IROpcode.GT,
    "<=": IROpcode.LTE,
    ">=": IROpcode.GTE,
    "&&": IROpcode.AND,
    "||": IROpcode.OR,
}


@dataclass
class IRInstruction:
    """A single three-address code instruction."""
    opcode: IROpcode
    dest: str | None = None      # destination variable / label
    src1: str | None = None      # first source operand
    src2: str | None = None      # second source operand

    def __repr__(self) -> str:
        return format_instruction(self)

    def is_jump(self) -> bool:
        return self.opcode in (IROpcode.JUMP, IROpcode.JUMP_IF_TRUE, IROpcode.JUMP_IF_FALSE)

    def is_label(self) -> bool:
        return self.opcode == IROpcode.LABEL

    def defined_var(self) -> str | None:
        """Return the variable defined (written) by this instruction, if any."""
        if self.opcode in (
            IROpcode.ADD, IROpcode.SUB, IROpcode.MUL, IROpcode.DIV,
            IROpcode.MOD, IROpcode.NEG,
            IROpcode.EQ, IROpcode.NEQ, IROpcode.LT, IROpcode.GT,
            IROpcode.LTE, IROpcode.GTE,
            IROpcode.AND, IROpcode.OR, IROpcode.NOT,
            IROpcode.COPY, IROpcode.LOAD_CONST, IROpcode.CALL,
        ):
            return self.dest
        return None

    def used_vars(self) -> set[str]:
        """Return the set of variables read by this instruction."""
        used: set[str] = set()
        if self.opcode in (
            IROpcode.ADD, IROpcode.SUB, IROpcode.MUL, IROpcode.DIV,
            IROpcode.MOD,
            IROpcode.EQ, IROpcode.NEQ, IROpcode.LT, IROpcode.GT,
            IROpcode.LTE, IROpcode.GTE,
            IROpcode.AND, IROpcode.OR,
        ):
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
            if self.src2 and not _is_constant(self.src2):
                used.add(self.src2)
        elif self.opcode in (IROpcode.NEG, IROpcode.NOT):
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        elif self.opcode == IROpcode.COPY:
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        elif self.opcode in (IROpcode.JUMP_IF_TRUE, IROpcode.JUMP_IF_FALSE):
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        elif self.opcode == IROpcode.PARAM:
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        elif self.opcode == IROpcode.RETURN:
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        elif self.opcode == IROpcode.PRINT:
            if self.src1 and not _is_constant(self.src1):
                used.add(self.src1)
        return used


def _is_constant(operand: str) -> bool:
    """Check if an operand is an integer constant (possibly negative)."""
    if operand.startswith("-"):
        return operand[1:].isdigit()
    return operand.isdigit()


def is_constant(operand: str) -> bool:
    """Public helper — check if an operand is a literal integer."""
    return _is_constant(operand)


def const_value(operand: str) -> int:
    """Parse an integer constant operand."""
    return int(operand)


def format_instruction(inst: IRInstruction) -> str:
    """Pretty-print a single IR instruction."""
    op = inst.opcode

    if op == IROpcode.LABEL:
        return f"{inst.dest}:"
    if op == IROpcode.JUMP:
        return f"  goto {inst.dest}"
    if op == IROpcode.JUMP_IF_TRUE:
        return f"  if {inst.src1} goto {inst.dest}"
    if op == IROpcode.JUMP_IF_FALSE:
        return f"  iffalse {inst.src1} goto {inst.dest}"
    if op == IROpcode.LOAD_CONST:
        return f"  {inst.dest} = {inst.src1}"
    if op == IROpcode.COPY:
        return f"  {inst.dest} = {inst.src1}"
    if op == IROpcode.NEG:
        return f"  {inst.dest} = -{inst.src1}"
    if op == IROpcode.NOT:
        return f"  {inst.dest} = !{inst.src1}"
    if op == IROpcode.PARAM:
        return f"  param {inst.src1}"
    if op == IROpcode.CALL:
        return f"  {inst.dest} = call {inst.src1}, {inst.src2}"
    if op == IROpcode.RETURN:
        if inst.src1:
            return f"  return {inst.src1}"
        return "  return"
    if op == IROpcode.PRINT:
        return f"  print {inst.src1}"
    if op == IROpcode.FUNC_BEGIN:
        return f"func {inst.dest}:"
    if op == IROpcode.FUNC_END:
        return f"end func {inst.dest}"
    if op == IROpcode.FUNC_PARAM:
        return f"  param_decl {inst.dest}"
    if op == IROpcode.NOP:
        return "  nop"

    # Binary ops
    symbols = {
        IROpcode.ADD: "+", IROpcode.SUB: "-", IROpcode.MUL: "*",
        IROpcode.DIV: "/", IROpcode.MOD: "%",
        IROpcode.EQ: "==", IROpcode.NEQ: "!=",
        IROpcode.LT: "<", IROpcode.GT: ">",
        IROpcode.LTE: "<=", IROpcode.GTE: ">=",
        IROpcode.AND: "&&", IROpcode.OR: "||",
    }
    sym = symbols.get(op, "?")
    return f"  {inst.dest} = {inst.src1} {sym} {inst.src2}"


def format_ir(instructions: list[IRInstruction]) -> str:
    """Pretty-print a full IR program."""
    return "\n".join(format_instruction(i) for i in instructions if i.opcode != IROpcode.NOP)
