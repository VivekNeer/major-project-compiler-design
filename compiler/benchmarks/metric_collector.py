"""
Metric Collector for benchmarking phase-ordering trade-offs.

Collects two primary metrics from optimized IR:

1. **Code Size** — number of meaningful IR instructions (excluding
   labels, NOPs, and structural markers).

2. **Estimated Performance** — weighted sum of instruction costs.
   Different instruction types have different latencies on real
   hardware; we model this with a simple cost table derived from
   typical RISC processor cycle counts.

These metrics allow plotting the trade-off space between code size
and execution speed for different optimization orderings.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from compiler.ir import IRInstruction, IROpcode


# Instruction cost model (approximate cycle counts on a simple RISC core).
# Based on ARM Cortex-M class processors common in embedded/MiBench targets.
INSTRUCTION_COST: dict[IROpcode, float] = {
    # Arithmetic — single-cycle ALU
    IROpcode.ADD:        1.0,
    IROpcode.SUB:        1.0,
    IROpcode.MUL:        3.0,    # multiply is typically 3 cycles
    IROpcode.DIV:        12.0,   # division is expensive
    IROpcode.MOD:        12.0,
    IROpcode.NEG:        1.0,

    # Comparison — single-cycle
    IROpcode.EQ:         1.0,
    IROpcode.NEQ:        1.0,
    IROpcode.LT:         1.0,
    IROpcode.GT:         1.0,
    IROpcode.LTE:        1.0,
    IROpcode.GTE:        1.0,

    # Logical — single-cycle
    IROpcode.AND:        1.0,
    IROpcode.OR:         1.0,
    IROpcode.NOT:        1.0,

    # Data movement — single-cycle register ops
    IROpcode.COPY:       1.0,
    IROpcode.LOAD_CONST: 1.0,

    # Control flow
    IROpcode.JUMP:           2.0,   # branch penalty
    IROpcode.JUMP_IF_TRUE:   2.0,
    IROpcode.JUMP_IF_FALSE:  2.0,
    IROpcode.LABEL:          0.0,   # not a real instruction

    # Function operations
    IROpcode.PARAM:      1.0,
    IROpcode.CALL:       5.0,   # call overhead
    IROpcode.RETURN:     3.0,   # return overhead

    # I/O
    IROpcode.PRINT:      10.0,  # I/O is slow

    # Structure
    IROpcode.FUNC_BEGIN: 0.0,
    IROpcode.FUNC_END:   0.0,
    IROpcode.FUNC_PARAM: 0.0,
    IROpcode.NOP:        0.0,
}


@dataclass
class BenchmarkMetrics:
    """Collected metrics for a single optimization ordering."""
    pass_order: list[str]
    pass_order_label: str
    code_size: int                 # static: number of real instructions
    estimated_cycles: float        # static: weighted cost sum
    total_instructions: int        # total including structural markers
    instruction_breakdown: dict[str, int]  # count per opcode category
    dynamic_instruction_count: int = 0     # dynamic: instructions actually executed
    dynamic_opcode_frequency: dict[str, int] = field(default_factory=dict)
    output_correct: bool = True            # whether output matches baseline

    @property
    def cycles_per_instruction(self) -> float:
        if self.code_size == 0:
            return 0.0
        return self.estimated_cycles / self.code_size


def count_code_size(instructions: list[IRInstruction]) -> int:
    """Count meaningful instructions (exclude labels, NOPs, structural markers)."""
    skip = {IROpcode.LABEL, IROpcode.NOP, IROpcode.FUNC_BEGIN, IROpcode.FUNC_END, IROpcode.FUNC_PARAM}
    return sum(1 for inst in instructions if inst.opcode not in skip)


def estimate_cycles(instructions: list[IRInstruction]) -> float:
    """Estimate total execution cost using the weighted cost model."""
    return sum(INSTRUCTION_COST.get(inst.opcode, 1.0) for inst in instructions)


def instruction_breakdown(instructions: list[IRInstruction]) -> dict[str, int]:
    """Count instructions by category."""
    categories: dict[str, int] = {
        "arithmetic": 0,
        "comparison": 0,
        "logical": 0,
        "data_movement": 0,
        "control_flow": 0,
        "function": 0,
        "io": 0,
    }

    arith = {IROpcode.ADD, IROpcode.SUB, IROpcode.MUL, IROpcode.DIV, IROpcode.MOD, IROpcode.NEG}
    comp = {IROpcode.EQ, IROpcode.NEQ, IROpcode.LT, IROpcode.GT, IROpcode.LTE, IROpcode.GTE}
    logic = {IROpcode.AND, IROpcode.OR, IROpcode.NOT}
    data = {IROpcode.COPY, IROpcode.LOAD_CONST}
    ctrl = {IROpcode.JUMP, IROpcode.JUMP_IF_TRUE, IROpcode.JUMP_IF_FALSE, IROpcode.LABEL}
    func = {IROpcode.PARAM, IROpcode.CALL, IROpcode.RETURN, IROpcode.FUNC_BEGIN, IROpcode.FUNC_END, IROpcode.FUNC_PARAM}
    io = {IROpcode.PRINT}

    for inst in instructions:
        if inst.opcode in arith:
            categories["arithmetic"] += 1
        elif inst.opcode in comp:
            categories["comparison"] += 1
        elif inst.opcode in logic:
            categories["logical"] += 1
        elif inst.opcode in data:
            categories["data_movement"] += 1
        elif inst.opcode in ctrl:
            categories["control_flow"] += 1
        elif inst.opcode in func:
            categories["function"] += 1
        elif inst.opcode in io:
            categories["io"] += 1

    return categories


def collect_metrics(
    instructions: list[IRInstruction],
    pass_order: list[str],
    dynamic_instruction_count: int = 0,
    dynamic_opcode_frequency: dict[str, int] | None = None,
    output_correct: bool = True,
) -> BenchmarkMetrics:
    """Collect all metrics for a given optimization result."""
    label = " -> ".join(pass_order) if pass_order else "Baseline (none)"
    return BenchmarkMetrics(
        pass_order=pass_order,
        pass_order_label=label,
        code_size=count_code_size(instructions),
        estimated_cycles=estimate_cycles(instructions),
        total_instructions=len(instructions),
        instruction_breakdown=instruction_breakdown(instructions),
        dynamic_instruction_count=dynamic_instruction_count,
        dynamic_opcode_frequency=dynamic_opcode_frequency or {},
        output_correct=output_correct,
    )
