"""Canonical KG id generator (course-provided; do not modify)."""

import re

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def canonical_id(label: str, name: str) -> str:
    """Return the canonical KG id for a (label, name) pair.

    Convention: '<label-lower>:<name-slug>'. Examples:
      canonical_id("Ingredient", "Orange")  -> "ingredient:orange"
      canonical_id("Cuisine", "Sichuan")    -> "cuisine:sichuan"
      canonical_id("Author", "Maria Rossi") -> "author:maria-rossi"
    """
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return f"{label.strip().lower()}:{slug}"
