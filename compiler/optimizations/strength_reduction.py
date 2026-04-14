"""
Strength Reduction (SR) Optimization Pass.

Replaces expensive operations with cheaper equivalents:
  - Multiplication by power of 2  ->  repeated addition (x * 2 = x + x)
  - Division by power of 2        ->  (kept as division, but flagged)
  - Multiplication by 0           ->  load constant 0
  - Multiplication by 1           ->  copy
  - Addition / subtraction of 0   ->  copy (identity elimination)

This pass interacts with Constant Folding: CF may fold expressions
that expose strength-reduction opportunities (e.g., after CF folds
`2+2` to `4`, SR can transform `x*4` to `x+x` applied twice, or
a chain of additions).

In real compilers on RISC architectures, multiply instructions cost
3-12x more cycles than add instructions, making this a significant
optimisation for embedded targets (ARM Cortex-M, the MiBench
reference platform).

Example:
    t1 = x * 2    ->   t1 = x + x
    t2 = y * 1    ->   t2 = y          (copy)
    t3 = z * 0    ->   t3 = 0          (constant)
    t4 = w + 0    ->   t4 = w          (identity)
"""

from __future__ import annotations
from compiler.ir import IRInstruction, IROpcode, is_constant, const_value


def strength_reduction(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Apply strength-reduction transformations.

    Returns a new list of instructions.
    """
    result: list[IRInstruction] = []

    for inst in instructions:
        reduced = _reduce(inst)
        result.append(reduced)

    return result


def _reduce(inst: IRInstruction) -> IRInstruction:
    """Try to reduce a single instruction to a cheaper form."""

    # --- Multiplication ---
    if inst.opcode == IROpcode.MUL and inst.dest:
        return _reduce_mul(inst)

    # --- Division ---
    if inst.opcode == IROpcode.DIV and inst.dest:
        return _reduce_div(inst)

    # --- Modulo ---
    if inst.opcode == IROpcode.MOD and inst.dest:
        return _reduce_mod(inst)

    # --- Addition ---
    if inst.opcode == IROpcode.ADD and inst.dest:
        return _reduce_add(inst)

    # --- Subtraction ---
    if inst.opcode == IROpcode.SUB and inst.dest:
        return _reduce_sub(inst)

    return inst


def _reduce_mul(inst: IRInstruction) -> IRInstruction:
    """Reduce multiplication."""
    s1, s2 = inst.src1, inst.src2

    # x * 0 = 0 (either operand)
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")
    if s2 and is_constant(s2) and const_value(s2) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # x * 1 = x (either operand)
    if s1 and is_constant(s1) and const_value(s1) == 1:
        return IRInstruction(IROpcode.COPY, inst.dest, s2)
    if s2 and is_constant(s2) and const_value(s2) == 1:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    # x * 2 = x + x (either operand)
    if s2 and is_constant(s2) and const_value(s2) == 2:
        return IRInstruction(IROpcode.ADD, inst.dest, s1, s1)
    if s1 and is_constant(s1) and const_value(s1) == 2:
        return IRInstruction(IROpcode.ADD, inst.dest, s2, s2)

    # x * -1 = -x
    if s2 and is_constant(s2) and const_value(s2) == -1:
        return IRInstruction(IROpcode.NEG, inst.dest, s1)
    if s1 and is_constant(s1) and const_value(s1) == -1:
        return IRInstruction(IROpcode.NEG, inst.dest, s2)

    return inst


def _reduce_div(inst: IRInstruction) -> IRInstruction:
    """Reduce division."""
    s1, s2 = inst.src1, inst.src2

    # x / 1 = x
    if s2 and is_constant(s2) and const_value(s2) == 1:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    # 0 / x = 0
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # x / x = 1 (when both are the same variable, not constants)
    if s1 and s2 and s1 == s2 and not is_constant(s1):
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "1")

    return inst


def _reduce_mod(inst: IRInstruction) -> IRInstruction:
    """Reduce modulo."""
    s1, s2 = inst.src1, inst.src2

    # x % 1 = 0
    if s2 and is_constant(s2) and const_value(s2) == 1:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # 0 % x = 0
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    # x % x = 0
    if s1 and s2 and s1 == s2 and not is_constant(s1):
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    return inst


def _reduce_add(inst: IRInstruction) -> IRInstruction:
    """Reduce addition (identity elimination)."""
    s1, s2 = inst.src1, inst.src2

    # x + 0 = x
    if s2 and is_constant(s2) and const_value(s2) == 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)
    if s1 and is_constant(s1) and const_value(s1) == 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s2)

    return inst


def _reduce_sub(inst: IRInstruction) -> IRInstruction:
    """Reduce subtraction (identity elimination)."""
    s1, s2 = inst.src1, inst.src2

    # x - 0 = x
    if s2 and is_constant(s2) and const_value(s2) == 0:
        return IRInstruction(IROpcode.COPY, inst.dest, s1)

    # x - x = 0
    if s1 and s2 and s1 == s2 and not is_constant(s1):
        return IRInstruction(IROpcode.LOAD_CONST, inst.dest, "0")

    return inst
