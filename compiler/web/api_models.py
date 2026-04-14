"""Pydantic request/response models for the web API."""
from __future__ import annotations
from pydantic import BaseModel


class CompileRequest(BaseModel):
    source: str


class OptimizeRequest(BaseModel):
    source: str
    pass_order: list[str]


class BenchmarkRequest(BaseModel):
    source: str
