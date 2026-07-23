"""Deterministic NL→Cypher mapper for the recipe KG.

Production-discipline implementation of schema-bounded NL→code generation:
fifteen canonical question shapes, each with a hand-authored, parameterized
Cypher template. Out-of-scope questions raise UnsupportedQueryError —
fail-loud is part of the contract.
"""

from .errors import UnsupportedQueryError
from .shapes import ShapeId, CANONICAL_CYPHER
from .intent import detect_shape
from .slots import extract_slots
from .compile import compile_to_cypher

__all__ = [
    "UnsupportedQueryError",
    "ShapeId",
    "CANONICAL_CYPHER",
    "detect_shape",
    "extract_slots",
    "compile_to_cypher",
]
