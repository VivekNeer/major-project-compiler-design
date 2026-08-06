"""Shared exception hierarchy for all compiler phases.

Every phase-specific error (lexer, parser, symbol table, semantic
analyzer, IR generator) derives from CompilerError so that drivers
(CLI, web API) can catch the whole family with one except clause.
"""
from __future__ import annotations


class CompilerError(Exception):
    """Base class for all user-facing compilation errors."""
