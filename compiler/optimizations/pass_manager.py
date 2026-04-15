"""
Optimization Pass Manager.

Orchestrates the execution of optimization passes in a configurable
order. This is the key component for benchmarking phase-ordering
trade-offs: the same IR can be optimized with different pass
sequences to measure how ordering affects code size and performance.
"""

from __future__ import annotations
from itertools import permutations
from typing import Callable

from compiler.ir import IRInstruction
from compiler.optimizations.constant_folding import constant_folding
from compiler.optimizations.dead_code_elimination import dead_code_elimination
from compiler.optimizations.common_subexpression_elimination import (
    common_subexpression_elimination,
)
from compiler.optimizations.copy_propagation import copy_propagation
from compiler.optimizations.strength_reduction import strength_reduction
from compiler.optimizations.algebraic_simplification import algebraic_simplification


# Registry of available optimization passes
PASS_REGISTRY: dict[str, Callable[[list[IRInstruction]], list[IRInstruction]]] = {
    "CF":  constant_folding,
    "DCE": dead_code_elimination,
    "CSE": common_subexpression_elimination,
    "CP":  copy_propagation,
    "SR":  strength_reduction,
    "AS":  algebraic_simplification,
}

# Human-readable names
PASS_NAMES: dict[str, str] = {
    "CF":  "Constant Folding",
    "DCE": "Dead Code Elimination",
    "CSE": "Common Subexpression Elimination",
    "CP":  "Copy Propagation",
    "SR":  "Strength Reduction",
    "AS":  "Algebraic Simplification",
}


class PassManager:
    """Runs optimization passes in a specified order."""

    def __init__(self, pass_names: list[str] | None = None):
        """Initialize with a list of pass short names (e.g. ["CF", "DCE", "CSE"]).
        If None, no passes are applied.
        """
        self.pass_names: list[str] = pass_names or []
        self._validate()

    def _validate(self) -> None:
        for name in self.pass_names:
            if name not in PASS_REGISTRY:
                raise ValueError(
                    f"Unknown optimization pass '{name}'. "
                    f"Available: {list(PASS_REGISTRY.keys())}"
                )

    def run(self, instructions: list[IRInstruction]) -> list[IRInstruction]:
        """Apply the pass sequence to the IR and return the optimized result."""
        result = list(instructions)  # don't mutate original
        for name in self.pass_names:
            pass_fn = PASS_REGISTRY[name]
            result = pass_fn(result)
        return result

    def describe(self) -> str:
        """Return a human-readable description of the pass order."""
        if not self.pass_names:
            return "No optimizations (baseline)"
        names = [PASS_NAMES.get(n, n) for n in self.pass_names]
        return " -> ".join(names)

    @staticmethod
    def all_orderings(pass_names: list[str] | None = None) -> list[list[str]]:
        """Generate all permutations of the given passes.

        Also includes the empty list (no optimization) as baseline,
        plus single-pass and two-pass combinations.
        """
        if pass_names is None:
            pass_names = list(PASS_REGISTRY.keys())

        orderings: list[list[str]] = [[]]  # baseline: no passes

        # All lengths from 1 to n
        for length in range(1, len(pass_names) + 1):
            for perm in permutations(pass_names, length):
                orderings.append(list(perm))

        return orderings

    @staticmethod
    def all_full_orderings(pass_names: list[str] | None = None) -> list[list[str]]:
        """Generate only the full-length permutations (all passes used)."""
        if pass_names is None:
            pass_names = list(PASS_REGISTRY.keys())

        orderings: list[list[str]] = [[]]  # baseline
        for perm in permutations(pass_names):
            orderings.append(list(perm))
        return orderings
