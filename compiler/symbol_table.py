"""
Symbol Table.

Manages variable names, types, and lexical scopes. Supports nested
scopes via a stack of dictionaries — entering a block pushes a new
scope; leaving it pops.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Symbol:
    """A single symbol entry."""
    name: str
    var_type: str = "int"       # Our language only has int for now
    scope_depth: int = 0
    ir_name: str = ""           # The name used in IR (may differ for shadowed vars)


class SymbolTableError(Exception):
    pass


class SymbolTable:
    """Nested-scope symbol table implemented as a scope stack."""

    def __init__(self) -> None:
        self._scopes: list[dict[str, Symbol]] = [{}]  # global scope
        self._depth: int = 0
        self._rename_counter: int = 0

    @property
    def depth(self) -> int:
        return self._depth

    def enter_scope(self) -> None:
        """Push a new scope (entering a block)."""
        self._depth += 1
        self._scopes.append({})

    def exit_scope(self) -> None:
        """Pop the current scope (leaving a block)."""
        if self._depth == 0:
            raise SymbolTableError("Cannot exit the global scope")
        self._scopes.pop()
        self._depth -= 1

    def declare(self, name: str, var_type: str = "int") -> Symbol:
        """Declare a new variable in the current scope.

        If the name already exists in the *current* scope, raise an error.
        Shadowing from an outer scope is allowed.
        """
        current = self._scopes[-1]
        if name in current:
            raise SymbolTableError(
                f"Variable '{name}' already declared in current scope"
            )

        # Generate a unique IR name to handle shadowing
        if self._depth == 0 and name not in self._all_names():
            ir_name = name
        else:
            # Check if we need a unique name
            if self._lookup_in_outer(name) is not None:
                self._rename_counter += 1
                ir_name = f"{name}_{self._rename_counter}"
            else:
                ir_name = name

        sym = Symbol(
            name=name,
            var_type=var_type,
            scope_depth=self._depth,
            ir_name=ir_name,
        )
        current[name] = sym
        return sym

    def lookup(self, name: str) -> Symbol:
        """Look up a variable by name, searching from innermost scope outward."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        raise SymbolTableError(f"Undeclared variable '{name}'")

    def _lookup_in_outer(self, name: str) -> Symbol | None:
        """Look up in scopes *below* the current one."""
        for scope in reversed(self._scopes[:-1]):
            if name in scope:
                return scope[name]
        return None

    def _all_names(self) -> set[str]:
        """Get all variable names across all scopes."""
        names: set[str] = set()
        for scope in self._scopes:
            names.update(scope.keys())
        return names

    def all_symbols(self) -> list[Symbol]:
        """Return all currently-visible symbols (innermost shadows outer)."""
        merged: dict[str, Symbol] = {}
        for scope in self._scopes:
            merged.update(scope)
        return list(merged.values())
