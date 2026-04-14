"""
Copy Propagation (CP) Optimization Pass.

Replaces uses of a variable with the source of its copy assignment,
when the variable was assigned via a simple COPY instruction and
neither the source nor destination has been redefined between the
copy and the use.

This pass creates rich phase-ordering interactions:
  - CSE often introduces COPY instructions (t5 = t0), which CP
    can then propagate, potentially enabling further DCE.
  - Running CP before CF can expose more constant-propagation
    opportunities.

Algorithm:
1. Maintain a map: dest -> src for active COPY instructions.
2. For each instruction, substitute any source operand that appears
   in the copy map with the propagated value.
3. Invalidate map entries when the source or destination is redefined.
4. Clear the map at control-flow boundaries (labels, jumps).

Example:
    t0 = a + b
    t1 = t0          (COPY)
    t2 = t1 + c      ->  t2 = t0 + c   (propagated)
"""

from __future__ import annotations
from compiler.ir import IRInstruction, IROpcode, is_constant


def copy_propagation(instructions: list[IRInstruction]) -> list[IRInstruction]:
    """Propagate copy assignments through subsequent uses.

    Returns a new list of instructions.
    """
    # copy_map: variable -> its copy source (transitive)
    copy_map: dict[str, str] = {}
    result: list[IRInstruction] = []

    for inst in instructions:
        # Control-flow boundaries: conservatively clear
        if inst.opcode in (
            IROpcode.LABEL, IROpcode.JUMP, IROpcode.JUMP_IF_TRUE,
            IROpcode.JUMP_IF_FALSE, IROpcode.CALL,
            IROpcode.FUNC_BEGIN, IROpcode.FUNC_END,
        ):
            copy_map.clear()
            result.append(inst)
            continue

        # Record COPY instructions: dest = src
        if inst.opcode == IROpcode.COPY and inst.dest and inst.src1:
            # Resolve src1 through existing copy chain
            resolved_src = _resolve(inst.src1, copy_map)

            # Invalidate any entries where dest was the source
            _invalidate(inst.dest, copy_map)

            # Record the new copy
            copy_map[inst.dest] = resolved_src

            result.append(IRInstruction(IROpcode.COPY, inst.dest, resolved_src))
            continue

        # For LOAD_CONST, the dest gets a new value — record it as a
        # constant "copy" so downstream uses can be substituted
        if inst.opcode == IROpcode.LOAD_CONST and inst.dest and inst.src1:
            _invalidate(inst.dest, copy_map)
            copy_map[inst.dest] = inst.src1
            result.append(inst)
            continue

        # Substitute operands in all other instructions
        new_inst = _substitute(inst, copy_map)

        # If this instruction defines a variable, invalidate its copy entry
        defined = new_inst.defined_var()
        if defined:
            _invalidate(defined, copy_map)

        result.append(new_inst)

    return result


def _resolve(name: str, copy_map: dict[str, str]) -> str:
    """Follow the copy chain to the root value."""
    seen: set[str] = set()
    current = name
    while current in copy_map and current not in seen:
        seen.add(current)
        current = copy_map[current]
    return current


def _invalidate(var: str, copy_map: dict[str, str]) -> None:
    """Remove all entries that depend on `var` (as source or dest)."""
    # Remove where var is the destination
    copy_map.pop(var, None)
    # Remove where var is the source (someone else copied from var)
    to_remove = [k for k, v in copy_map.items() if v == var]
    for k in to_remove:
        del copy_map[k]


def _substitute(inst: IRInstruction, copy_map: dict[str, str]) -> IRInstruction:
    """Replace source operands using the copy map."""
    new_src1 = inst.src1
    new_src2 = inst.src2
    changed = False

    if inst.src1 and not is_constant(inst.src1) and inst.src1 in copy_map:
        new_src1 = copy_map[inst.src1]
        changed = True

    if inst.src2 and not is_constant(inst.src2) and inst.src2 in copy_map:
        new_src2 = copy_map[inst.src2]
        changed = True

    if changed:
        return IRInstruction(inst.opcode, inst.dest, new_src1, new_src2)
    return inst
