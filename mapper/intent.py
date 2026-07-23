"""Intent classifier — map NL question to a canonical ShapeId.

Classifies questions into one of 15 canonical shapes using keyword/regex rules.
Priority order: more-specific patterns before less-specific to avoid shadowing.
"""
import re

from .shapes import ShapeId

# Top-level abstract cuisines that trigger hierarchy traversal when queried alone (Q3 vs Q4)
# These are the abstract categories that users expect to return all descendants
TOP_LEVEL_CUISINES = {
    "asian",
    "european",
    "americas",
}

# All cuisines that have children (used for Q5 vs Q6 distinction with ingredients)
PARENT_CUISINES = {
    "asian",
    "european",
    "americas",
    "chinese",
    "italian",
}

# All 16 cuisines in canonical form
CUISINE_VOCAB = {
    "world", "asian", "european", "americas", "chinese", "japanese",
    "indian", "thai", "sichuan", "italian", "french", "spanish",
    "tuscan", "sicilian", "mexican", "northamerican",
}

# All 40 ingredients in canonical form
INGREDIENT_VOCAB = {
    "ginger", "garlic", "basil", "orange", "turkey", "sage", "salt",
    "pepper", "peppercorn", "szechuan peppercorn", "chili", "tomato",
    "onion", "scallion", "soy sauce", "rice", "rice noodles",
    "wheat noodles", "egg", "chicken", "beef", "pork", "tofu",
    "shrimp", "fish", "lemon", "lime", "cilantro", "parsley",
    "thyme", "rosemary", "oregano", "flour", "butter", "cheese",
    "cream", "milk", "olive oil", "sesame oil", "vinegar",
}

# All 12 techniques in canonical form
TECHNIQUE_VOCAB = {
    "wok", "braise", "saute", "roast", "grill", "steam",
    "fry", "bake", "boil", "simmer", "smoke", "poach",
}


def _is_top_level_cuisine(cuisine: str) -> bool:
    """Check if a cuisine is a top-level abstract category (triggers hierarchy for Q3/Q4)."""
    return cuisine.lower() in TOP_LEVEL_CUISINES


def _is_parent_cuisine(cuisine: str) -> bool:
    """Check if a cuisine has children (used for Q5/Q6 distinction)."""
    return cuisine.lower() in PARENT_CUISINES


def _find_cuisine(question_lower: str) -> str | None:
    """Find a cuisine name in the question (case-insensitive)."""
    for cuisine in sorted(CUISINE_VOCAB, key=len, reverse=True):
        if cuisine in question_lower:
            return cuisine
    return None


def _find_ingredient(question_lower: str, exclude: set[str] = frozenset()) -> str | None:
    """Find an ingredient name in the question (case-insensitive, excluding specified ones)."""
    # Sort by length descending to match longer names first (e.g., "szechuan peppercorn" before "peppercorn")
    for ingredient in sorted(INGREDIENT_VOCAB, key=len, reverse=True):
        if ingredient in question_lower and ingredient not in exclude:
            return ingredient
    return None


def _find_technique(question_lower: str) -> str | None:
    """Find a technique name in the question (case-insensitive)."""
    for technique in TECHNIQUE_VOCAB:
        if technique in question_lower:
            return technique
    return None


def detect_shape(question: str) -> ShapeId | None:
    """Classify question into one of 15 canonical shapes.
    
    Apply detection rules in priority order:
      1. More-specific shapes before less-specific (e.g., q14 before q1)
      2. Conjunctions before single-hops
      3. Negation patterns before positive patterns
    
    Returns None if the question doesn't match any supported shape.
    """
    question_lower = question.lower()
    
    # Q14: "use X but not Y" (must be before Q1, Q8)
    if "but not" in question_lower or "without" in question_lower:
        # Split on the negation word to find positive and negative ingredients
        if "but not" in question_lower:
            parts = question_lower.split("but not")
        else:
            parts = question_lower.split("without")
        
        positive_part = parts[0]
        negative_part = parts[1] if len(parts) > 1 else ""
        
        # Find positive ingredient
        ingredient = _find_ingredient(positive_part)
        if ingredient:
            # Find negative ingredient
            exclude_ingredient = _find_ingredient(negative_part)
            if exclude_ingredient and exclude_ingredient != ingredient:
                return ShapeId.Q14
    
    # Q8: "by <author> that use <ingredient>" (must be before Q2, Q1)
    if "by" in question_lower and "that use" in question_lower:
        # This is a conjunction of author and ingredient
        ingredient = _find_ingredient(question_lower)
        if ingredient:
            return ShapeId.Q8
    
    # Q12: "authors of" + cuisine (must be before Q2)
    if "authors of" in question_lower:
        cuisine = _find_cuisine(question_lower)
        if cuisine:
            return ShapeId.Q12
    
    # Q15: "optionally tagged with" or "OPTIONAL" pattern
    if "optionally tagged with" in question_lower or "optionally" in question_lower:
        return ShapeId.Q15
    
    # Q10: "under N minutes"
    if "under" in question_lower and "minutes" in question_lower:
        match = re.search(r"under\s+(\d+)\s*minutes", question_lower)
        if match:
            return ShapeId.Q10
    
    # Q9: "ranked by popularity" or "most popular"
    if "ranked by popularity" in question_lower or "most popular" in question_lower:
        cuisine = _find_cuisine(question_lower)
        if cuisine:
            return ShapeId.Q9
    
    # Q11: "ingredients used in" (inverse pattern)
    if "ingredients used in" in question_lower or "ingredients" in question_lower and "used in" in question_lower:
        cuisine = _find_cuisine(question_lower)
        if cuisine:
            return ShapeId.Q11
    
    # Q7: "require <technique>"
    if "require" in question_lower:
        technique = _find_technique(question_lower)
        if technique:
            return ShapeId.Q7
    
    # Q13: "or any subtype" or "or any kind"
    if "or any subtype" in question_lower or "or any kind" in question_lower:
        ingredient = _find_ingredient(question_lower)
        if ingredient:
            return ShapeId.Q13
    
    # Q6: cuisine hierarchy + ingredient (must be before Q5, Q3, Q1)
    cuisine = _find_cuisine(question_lower)
    ingredient = _find_ingredient(question_lower)
    if cuisine and ingredient:
        if _is_parent_cuisine(cuisine):
            return ShapeId.Q6
        else:
            return ShapeId.Q5
    
    # Q4: top-level cuisine hierarchy without ingredient (must be before Q3)
    if cuisine and _is_top_level_cuisine(cuisine):
        return ShapeId.Q4
    
    # Q3: cuisine direct (no hierarchy traversal) — for leaf cuisines or specific cuisines
    if cuisine:
        return ShapeId.Q3
    
    # Q2: "by author <name>" (must be before Q1)
    if "by" in question_lower:
        # This is a single author pattern
        return ShapeId.Q2
    
    # Q1: "use <ingredient>"
    if ingredient and ("use" in question_lower or "with" in question_lower):
        return ShapeId.Q1
    
    # No match found
    return None


def detect_shape(question: str) -> ShapeId | None:
    """Classify the question into one of the 15 ShapeId values, or None."""
    q = question.lower().strip()

    # --- q14: negation. Must fire before q1/q5/q6/q8 (all contain "use"). ---
    if re.search(r"\bbut not\b|\bwithout\b", q):
        return ShapeId.Q14

    # --- q15: optional-tagged technique. Fires before q7. ---
    if "optionally tagged" in q:
        return ShapeId.Q15

    # --- q10: prep-time filter. Numeric cue, unambiguous. ---
    if re.search(r"\bunder\s+\d+\s*minutes?\b", q):
        return ShapeId.Q10

    # --- q13: ingredient hierarchy ("or any subtype/kind"). ---
    if "or any subtype" in q or "or any kind" in q:
        return ShapeId.Q13

    # --- q11: inverse (ingredients used IN <cuisine> recipes). ---
    if "ingredients used in" in q:
        return ShapeId.Q11

    # --- q12: authors of <cuisine> recipes. ---
    if "authors of" in q:
        return ShapeId.Q12

    # --- q9: ranked / popularity. ---
    if "ranked by popularity" in q or "most popular" in q:
        return ShapeId.Q9

    # --- q7: technique requirement (not optional). ---
    if re.search(r"\brequire[s]?\b", q) and "technique" in q:
        return ShapeId.Q7

    # --- q8: author + ingredient conjunction. Must fire before q1/q2. ---
    has_author_cue = bool(re.search(r"\bby author\b|\bby [A-Z]", question))
    has_ingredient_cue = bool(re.search(r"\buse[s]?\b|\bwith\b", q))
    if has_author_cue and has_ingredient_cue:
        return ShapeId.Q8

    # --- q2: author only. ---
    if has_author_cue:
        return ShapeId.Q2

    # --- q5/q6: cuisine + ingredient conjunction. Must fire before q1/q3/q4. ---
    cuisine = _find_cuisine(q)
    ingredient_cue = bool(re.search(r"\buse[s]?\b|\bwith\b", q))
    if cuisine and ingredient_cue:
        ingredient = _find_ingredient(q, exclude={cuisine})
        if ingredient:
            return ShapeId.Q6 if _is_parent_cuisine(cuisine) else ShapeId.Q5

    # --- q3/q4: cuisine only. ---
    if cuisine:
        return ShapeId.Q4 if _is_parent_cuisine(cuisine) else ShapeId.Q3

    # --- q1: bare ingredient with "use"/"with" cue. ---
    if ingredient_cue:
        ingredient = _find_ingredient(q)
        if ingredient:
            return ShapeId.Q1

    # No rule fired -- off-template question.
    return None