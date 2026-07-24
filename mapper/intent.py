"""Intent classifier — map NL question to a canonical ShapeId.

Classifies questions into one of 15 canonical shapes using keyword/regex rules.
Priority order: more-specific patterns before less-specific to avoid shadowing.
"""
import re

from .shapes import ShapeId

# Top-level abstract cuisines that trigger hierarchy traversal when queried alone (Q4)
TOP_LEVEL_CUISINES = {
    "asian", "european", "americas", "world"
}

# Cuisines that have children (for Q5 vs Q6 with ingredients)
PARENT_CUISINES = {
    "asian", "european", "americas", "chinese"
    # "italian" removed - treated as leaf for Q3
}

# All 16 cuisines
CUISINE_VOCAB = {
    "world", "asian", "european", "americas", "chinese", "japanese",
    "indian", "thai", "sichuan", "italian", "french", "spanish",
    "tuscan", "sicilian", "mexican", "northamerican",
}

# ... (باقي الكود زي ما هو - INGREDIENT_VOCAB, TECHNIQUE_VOCAB, helpers)

def _is_top_level_cuisine(cuisine: str) -> bool:
    return cuisine.lower() in TOP_LEVEL_CUISINES


def _is_parent_cuisine(cuisine: str) -> bool:
    return cuisine.lower() in PARENT_CUISINES


# ... (الـ _find_* functions زي ما هي)


def detect_shape(question: str) -> ShapeId | None:
    """Classify the question into one of the 15 ShapeId values, or None."""
    q = question.lower().strip()

    # --- q14: negation ---
    if re.search(r"\bbut not\b|\bwithout\b", q):
        return ShapeId.Q14

    # --- q15, q10, q13, q11, q12, q9, q7, q8, q2 (كما هي) ---
    if "optionally tagged" in q:
        return ShapeId.Q15
    if re.search(r"\bunder\s+\d+\s*minutes?\b", q):
        return ShapeId.Q10
    if "or any subtype" in q or "or any kind" in q:
        return ShapeId.Q13
    if "ingredients used in" in q:
        return ShapeId.Q11
    if "authors of" in q:
        return ShapeId.Q12
    if "ranked by popularity" in q or "most popular" in q:
        return ShapeId.Q9
    if re.search(r"\brequire[s]?\b", q) and "technique" in q:
        return ShapeId.Q7

    has_author_cue = bool(re.search(r"\bby author\b|\bby [A-Z]", question))
    has_ingredient_cue = bool(re.search(r"\buse[s]?\b|\bwith\b", q))
    if has_author_cue and has_ingredient_cue:
        return ShapeId.Q8
    if has_author_cue:
        return ShapeId.Q2

    # --- cuisine + ingredient ---
    cuisine = _find_cuisine(q)
    if cuisine and has_ingredient_cue:
        return ShapeId.Q6 if _is_parent_cuisine(cuisine) else ShapeId.Q5

    # --- cuisine only ---
    if cuisine:
        return ShapeId.Q4 if _is_top_level_cuisine(cuisine) else ShapeId.Q3

    # --- q1 ---
    if has_ingredient_cue:
        ingredient = _find_ingredient(q)
        if ingredient:
            return ShapeId.Q1

    return None