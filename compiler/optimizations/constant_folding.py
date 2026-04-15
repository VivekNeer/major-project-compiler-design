"""
Constant Folding Optimization Pass.

Evaluates expressions whose operands are both compile-time constants,
replacing them with a single LOAD_CONST instruction. This reduces
runtime computation by performing arithmetic at compile time.

Example:
    t1 = 2          →   t1 = 2
    t2 = 3          →   t2 = 3
    t3 = t1 + t2    →   t3 = 5       (folded)

Also performs constant propagation: if a variable is assigned a
constant and is not reassigned before use, its value is substituted
directly into subsequent instructions.
"""

from __future__ import annotations
import operator
from compiler.ir import IRInstruction, IROpcode, is_constant, const_value


# Map opcodes to Python operators for evaluation
_EVAL_OPS: dict[IROpcode, object] = {
    IROpcode.ADD: operator.add,
    IROpcode.SUB: operator.sub,
    IROpcode.MUL: operator.mul,
    IROpcode.DIV: lambda a, b: a // b if b != 0 else 0,  # integer division, guard /0
    IROpcode.MOD: lambda a, b: a % b if b != 0 else 0,
    IROpcode.EQ:  lambda a, b: int(a == b),
    IROpcode.NEQ: lambda a, b: int(a != b),
    IROpcode.LT:  lambda a, b: int(a < b),
    IROpcode.GT:  lambda a, b: int(a > b),
    IROpcode.LTE: lambda a, b: int(a <= b),
    IROpcode.GTE: lambda a, b: int(a >= b),
    IROpcode.AND: lambda a, b: int(bool(a) and bool(b)),
    IROpcode.OR:  lambda a, b: int(bool(a) or bool(b)),
}

_UNARY_OPS: dict[IROpcode, object] = {
    IROpcode.NEG: operator.neg,
    IROpcode.NOT: lambda a: int(not a),
}

# Opcodes that are binary arithmetic/comparison
_BINARY_OPCODES = set(_EVAL_OPS.keys())
_UNARY_OPCODES = set(_UNARY_OPS.keys())


def constant_folding(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Run constant folding + constant propagation over the IR.

    Returns a new list of instructions (does not mutate the input).
    """
    # Phase 1: Build a constant map via propagation
    # A variable maps to a constant string if it is assigned exactly once
    # with a known constant value and never reassigned.
    const_map: dict[str, str] = {}
    assign_count: dict[str, int] = {}

    for inst in instructions:
        defined = inst.defined_var()
        if defined:
            assign_count[defined] = assign_count.get(defined, 0) + 1

    # First pass: find single-assignment constants
    for inst in instructions:
        if inst.opcode == IROpcode.LOAD_CONST and inst.dest:
            if assign_count.get(inst.dest, 0) == 1 and inst.src1 is not None:
                const_map[inst.dest] = inst.src1
        elif inst.opcode == IROpcode.COPY and inst.dest and inst.src1:
            if assign_count.get(inst.dest, 0) == 1 and is_constant(inst.src1):
                const_map[inst.dest] = inst.src1
            elif assign_count.get(inst.dest, 0) == 1 and inst.src1 in const_map:
                const_map[inst.dest] = const_map[inst.src1]

    # Phase 2: Substitute constants and fold
    result: list[IRInstruction] = []
    changed = True

    # Iterate to a fixed point
    working = list(instructions)
    while changed:
        changed = False
        new_result: list[IRInstruction] = []
        new_const_map: dict[str, str] = {}

        for inst in working:
            new_inst = _fold_instruction(inst, const_map)
            if new_inst != inst:
                changed = True
            new_result.append(new_inst)

            # Update const map
            if new_inst.opcode == IROpcode.LOAD_CONST and new_inst.dest:
                if assign_count.get(new_inst.dest, 0) == 1 and new_inst.src1 is not None:
                    new_const_map[new_inst.dest] = new_inst.src1

        const_map.update(new_const_map)
        working = new_result

    return working


def _resolve(operand: str | None, const_map: dict[str, str]) -> str | None:
    """Resolve an operand through the constant map."""
    if operand is None:
        return None
    if operand in const_map:
        return const_map[operand]
    return operand


def _fold_instruction(inst: IRInstruction, const_map: dict[str, str]) -> IRInstruction:
    """Try to fold a single instruction using known constants."""
    opcode = inst.opcode

    # --- Binary operations ---
    if opcode in _BINARY_OPCODES:
        s1 = _resolve(inst.src1, const_map)
        s2 = _resolve(inst.src2, const_map)

        if s1 is not None and s2 is not None and is_constant(s1) and is_constant(s2):
            fn = _EVAL_OPS[opcode]
            val = fn(const_value(s1), const_value(s2))
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, str(int(val)))

        # Even if we can't fully fold, propagate constants into operands
        new_src1 = s1 if s1 != inst.src1 else inst.src1
        new_src2 = s2 if s2 != inst.src2 else inst.src2
        if new_src1 != inst.src1 or new_src2 != inst.src2:
            return IRInstruction(opcode, inst.dest, new_src1, new_src2)
        return inst

    # --- Unary operations ---
    if opcode in _UNARY_OPCODES:
        s1 = _resolve(inst.src1, const_map)
        if s1 is not None and is_constant(s1):
            fn = _UNARY_OPS[opcode]
            val = fn(const_value(s1))
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, str(int(val)))

        if s1 != inst.src1:
            return IRInstruction(opcode, inst.dest, s1)
        return inst

    # --- COPY: propagate constant into copy source ---
    if opcode == IROpcode.COPY and inst.src1:
        s1 = _resolve(inst.src1, const_map)
        if s1 != inst.src1 and s1 is not None and is_constant(s1):
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, s1)
        return inst

    # --- Conditional jumps: if constant, convert to unconditional/remove ---
    if opcode == IROpcode.JUMP_IF_TRUE and inst.src1:
        s1 = _resolve(inst.src1, const_map)
        if s1 is not None and is_constant(s1):
            if const_value(s1):
                return IRInstruction(IROpcode.JUMP, inst.dest)
            else:
                return IRInstruction(IROpcode.NOP)
        return inst

    if opcode == IROpcode.JUMP_IF_FALSE and inst.src1:
        s1 = _resolve(inst.src1, const_map)
        if s1 is not None and is_constant(s1):
            if not const_value(s1):
                return IRInstruction(IROpcode.JUMP, inst.dest)
            else:
                return IRInstruction(IROpcode.NOP)
        return inst

    return inst
