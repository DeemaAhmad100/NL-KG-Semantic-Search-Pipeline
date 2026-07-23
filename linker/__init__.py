"""Bundled reference linker for the Integration repo.

This is a course-provided, complete implementation of the entity-linker
contract from the Applied Lab. The Integration repo ships this reference
linker (rather than re-depending on the learner's submitted Lab code) so
that an Integration-Task learner whose Lab linker fell short can still
complete the Integration. The contract surface (function signatures) is
stable and matches the Applied Lab's `linker/` module exactly.

Do not modify these files for the Integration deliverable.
"""

from .types import GoldSpan, LinkResult
from .identity import canonical_id
from .candidates import candidates
from .disambiguate import disambiguate, NER_LABEL_TO_KG_TYPE
from .link import link
from .score import score

__all__ = [
    "GoldSpan",
    "LinkResult",
    "canonical_id",
    "candidates",
    "disambiguate",
    "NER_LABEL_TO_KG_TYPE",
    "link",
    "score",
]
