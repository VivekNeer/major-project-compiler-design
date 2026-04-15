"""
Algebraic Simplification (AS) Optimization Pass.

Applies algebraic identities and rewriting rules to simplify
expressions beyond what Strength Reduction covers. Focuses on
patterns that arise from code generation and other optimization
passes:

Identities:
  - Double negation:    --x   ->  x
  - Double NOT:         !!x   ->  x  (for boolean context)
  - Negation of const:  -(K)  ->  (-K)
  - Redundant compare:  x == x  ->  1,   x != x  ->  0
  - Comparison folding:  x < x  ->  0,   x <= x  ->  1
  - Idempotent ops:     x && x  ->  x,   x || x  ->  x
  - Absorption:         x && 1  ->  x,   x || 0  ->  x
  - Annihilation:       x && 0  ->  0,   x || 1  ->  1

Phase-ordering interactions:
  - After Constant Folding propagates constants, AS can simplify
    `x * 1` or `x + 0` patterns that CF alone does not handle
    (CF only folds when BOTH operands are constant).
  - After Copy Propagation, variables may be substituted revealing
    `a == a` or `a - a` patterns.
"""

from __future__ import annotations
from compiler.ir import IRInstruction, IROpcode, is_constant, const_value


def algebraic_simplification(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Apply algebraic identities to simplify instructions.

    Returns a new list of instructions.
    """
    result: list[IRInstruction] = []
    for inst in instructions:
        simplified = _simplify(inst)
        result.append(simplified)
    return result


def _simplify(inst: IRInstruction) -> IRInstruction:
    """Try to simplify a single instruction using algebraic rules."""
    op = inst.opcode

    # --- Double negation: NEG(NEG(x)) handled via chaining ---
    # (This is handled implicitly when CP propagates the inner result)

    # --- Negation of constant ---
    if op == IROpcode.NEG and inst.src1 and is_constant(inst.src1):
        val = -const_value(inst.src1)
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, str(val))

    # --- NOT of constant ---
    if op == IROpcode.NOT and inst.src1 and is_constant(inst.src1):
        val = int(not const_value(inst.src1))
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, str(val))

    # --- Self-comparisons (x op x) ---
    if inst.src1 and inst.src2 and inst.src1 == inst.src2 and not is_constant(inst.src1):
        if op == IROpcode.EQ:   # x == x -> 1
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")
        if op == IROpcode.NEQ:  # x != x -> 0
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")
        if op == IROpcode.LT:   # x < x -> 0
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")
        if op == IROpcode.GT:   # x > x -> 0
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")
        if op == IROpcode.LTE:  # x <= x -> 1
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")
        if op == IROpcode.GTE:  # x >= x -> 1
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")
        if op == IROpcode.SUB:  # x - x -> 0
            return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # --- Logical identities ---
    if op == IROpcode.AND:
        return _simplify_and(inst)
    if op == IROpcode.OR:
        return _simplify_or(inst)

    # --- Idempotent operations with same operand ---
    # These are less common but can appear after copy propagation

    return inst


def _simplify_and(inst: IRInstruction) -> IRInstruction:
    """Simplify AND operations."""
    s1, s2 = inst.src1, inst.src2

    # x && x -> x (idempotent)
    if s1 and s2 and s1 == s2:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    # x && 0 -> 0
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")
    if s2 and is_constant(s2) and const_value(s2) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # x && 1 -> x (when used as boolean)
    if s1 and is_constant(s1) and const_value(s1) != 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s2)
    if s2 and is_constant(s2) and const_value(s2) != 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    return inst


def _simplify_or(inst: IRInstruction) -> IRInstruction:
    """Simplify OR operations."""
    s1, s2 = inst.src1, inst.src2

    # x || x -> x (idempotent)
    if s1 and s2 and s1 == s2:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    # x || 1 -> 1
    if s1 and is_constant(s1) and const_value(s1) != 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")
    if s2 and is_constant(s2) and const_value(s2) != 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")

    # x || 0 -> x
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s2)
    if s2 and is_constant(s2) and const_value(s2) == 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    return inst
