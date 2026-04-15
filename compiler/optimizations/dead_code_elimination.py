"""
Dead Code Elimination (DCE) Optimization Pass.

Removes instructions that compute values never used by any
subsequent instruction. Also removes unreachable code that
follows an unconditional jump (before the next label).

Algorithm (iterative liveness):
1. Mark all variables that are "used" — appear as a source operand
   in a PRINT, RETURN, PARAM, conditional jump, or as an operand
   in an instruction whose destination is itself used.
2. Walk backwards through the instruction list; any instruction that
   defines a variable not in the used set is dead and removed.
3. Repeat until no more instructions are removed (fixed-point).

Unreachable code removal:
- After an unconditional JUMP, all instructions until the next LABEL
  are unreachable and removed.
"""

from __future__ import annotations
from compiler.ir import IRInstruction, IROpcode


def dead_code_elimination(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Remove dead and unreachable code. Returns a new instruction list."""
    result = _remove_unreachable(instructions)
    result = _remove_dead_assignments(result)
    return result


def _remove_unreachable(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Remove instructions that follow an unconditional JUMP before a LABEL."""
    result: list[IRInstruction] = []
    unreachable = False

    for inst in instructions:
        if inst.opcode == IROpcode.LABEL:
            unreachable = False
        if inst.opcode == IROpcode.FUNC_BEGIN:
            unreachable = False
        if inst.opcode == IROpcode.FUNC_END:
            unreachable = False

        if not unreachable:
            result.append(inst)

        if inst.opcode == IROpcode.JUMP and not unreachable:
            unreachable = True
        if inst.opcode == IROpcode.RETURN and not unreachable:
            unreachable = True

    return result


def _remove_dead_assignments(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Iteratively remove assignments to variables that are never read.

    Preserves instructions with side effects (PRINT, CALL, RETURN,
    PARAM, jumps, labels, FUNC_BEGIN/END).
    """
    changed = True
    working = list(instructions)

    while changed:
        changed = False

        # Collect all used variables
        used: set[str] = set()
        for inst in working:
            used |= inst.used_vars()

        new_working: list[IRInstruction] = []
        for inst in working:
            if _is_dead(inst, used):
                changed = True
            else:
                new_working.append(inst)

        working = new_working

    return working


def _is_dead(inst: IRInstruction, used: set[str]) -> bool:
    """Determine if an instruction is dead (defines an unused variable
    and has no side effects)."""
    # Never remove these — they have side effects or structural meaning
    if inst.opcode in (
        IROpcode.PRINT, IROpcode.RETURN, IROpcode.PARAM,
        IROpcode.JUMP, IROpcode.JUMP_IF_TRUE, IROpcode.JUMP_IF_FALSE,
        IROpcode.LABEL, IROpcode.FUNC_BEGIN, IROpcode.FUNC_END,
        IROpcode.CALL,  # calls may have side effects
        IROpcode.NOP,
    ):
        return False

    defined = inst.defined_var()
    if defined is None:
        return False

    # A temp or variable that nobody reads is dead
    return defined not in used
