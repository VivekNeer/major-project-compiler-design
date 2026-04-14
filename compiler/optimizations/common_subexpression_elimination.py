"""
Common Subexpression Elimination (CSE) Optimization Pass.

Identifies expressions that have been computed previously with the
same operands, and reuses the earlier result instead of recomputing.

Algorithm:
1. Maintain an "available expressions" table mapping
   (opcode, src1, src2) → dest_variable.
2. For each instruction, check if the same expression already exists
   in the table. If so, replace the instruction with a COPY from the
   previously-computed result.
3. Invalidate table entries when their operands are redefined.
4. Clear the table at labels and jumps (conservative approach for
   control flow merges).

Example:
    t1 = a + b      →  t1 = a + b
    ...                  ...
    t5 = a + b      →  t5 = t1        (reused)
"""

from __future__ import annotations
from compiler.ir import IRInstruction, IROpcode


# Opcodes eligible for CSE — pure computations
_CSE_OPCODES = {
    IROpcode.ADD, IROpcode.SUB, IROpcode.MUL, IROpcode.DIV, IROpcode.MOD,
    IROpcode.EQ, IROpcode.NEQ, IROpcode.LT, IROpcode.GT,
    IROpcode.LTE, IROpcode.GTE,
    IROpcode.AND, IROpcode.OR,
    IROpcode.NEG, IROpcode.NOT,
}


def common_subexpression_elimination(
    instructions: list[IRInstruction],
) -> list[IRInstruction]:
    """Eliminate common subexpressions. Returns a new instruction list."""
    # available_exprs: (opcode, src1, src2) → variable holding the result
    available_exprs: dict[tuple[IROpcode, str | None, str | None], str] = {}

    # Track which variables map to which expression key, so we can
    # invalidate when the variable is redefined.
    var_to_expr_keys: dict[str, list[tuple[IROpcode, str | None, str | None]]] = {}

    result: list[IRInstruction] = []

    for inst in instructions:
        # Control flow boundaries: conservatively clear available expressions
        if inst.opcode in (
            IROpcode.LABEL, IROpcode.JUMP, IROpcode.JUMP_IF_TRUE,
            IROpcode.JUMP_IF_FALSE, IROpcode.CALL,
            IROpcode.FUNC_BEGIN, IROpcode.FUNC_END,
        ):
            available_exprs.clear()
            var_to_expr_keys.clear()
            result.append(inst)
            continue

        if inst.opcode in _CSE_OPCODES and inst.dest:
            expr_key = (inst.opcode, inst.src1, inst.src2)

            if expr_key in available_exprs:
                # Reuse the previously computed value
                prev_var = available_exprs[expr_key]
                result.append(IRInstruction(IROpcode.COPY, inst.dest, prev_var))
                # The new dest also holds this expression's value
                available_exprs[expr_key] = inst.dest
            else:
                result.append(inst)
                # Record this expression as available
                available_exprs[expr_key] = inst.dest

            # Invalidate any expressions that used the dest as an operand
            # (since we're redefining it)
            _invalidate_var(inst.dest, available_exprs, var_to_expr_keys)

            # Track operand → expression key mapping for invalidation
            for operand in (inst.src1, inst.src2):
                if operand and not operand.isdigit():
                    var_to_expr_keys.setdefault(operand, []).append(expr_key)

            continue

        # For other instructions, check if they redefine a variable
        defined = inst.defined_var()
        if defined:
            _invalidate_var(defined, available_exprs, var_to_expr_keys)

        result.append(inst)

    return result


def _invalidate_var(
    var: str,
    available_exprs: dict[tuple[IROpcode, str | None, str | None], str],
    var_to_expr_keys: dict[str, list[tuple[IROpcode, str | None, str | None]]],
) -> None:
    """Remove all available expressions that depend on `var`."""
    if var in var_to_expr_keys:
        for key in var_to_expr_keys[var]:
            available_exprs.pop(key, None)
        del var_to_expr_keys[var]
