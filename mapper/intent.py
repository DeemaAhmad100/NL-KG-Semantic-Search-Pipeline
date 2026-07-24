"""Intent classifier — map NL question to a canonical ShapeId."""

import re

from .shapes import ShapeId

TOP_LEVEL_CUISINES = {"asian", "european", "americas", "world"}
PARENT_CUISINES = {"asian", "european", "americas", "chinese"}

CUISINE_VOCAB = {
    "world", "asian", "european", "americas", "chinese", "japanese",
    "indian", "thai", "sichuan", "italian", "french", "spanish",
    "tuscan", "sicilian", "mexican", "northamerican",
}

INGREDIENT_VOCAB = {
    "ginger", "garlic", "basil", "orange", "turkey", "sage", "salt",
    "pepper", "peppercorn", "szechuan peppercorn", "chili", "tomato",
    "onion", "scallion", "soy sauce", "rice", "rice noodles",
    "wheat noodles", "egg", "chicken", "beef", "pork", "tofu",
    "shrimp", "fish", "lemon", "lime", "cilantro", "parsley",
    "thyme", "rosemary", "oregano", "flour", "butter", "cheese",
    "cream", "milk", "olive oil", "sesame oil", "vinegar",
}

TECHNIQUE_VOCAB = {
    "wok", "braise", "saute", "roast", "grill", "steam",
    "fry", "bake", "boil", "simmer", "smoke", "poach",
}


def _is_top_level_cuisine(cuisine: str) -> bool:
    return cuisine.lower() in TOP_LEVEL_CUISINES


def _is_parent_cuisine(cuisine: str) -> bool:
    return cuisine.lower() in PARENT_CUISINES


def _find_cuisine(question_lower: str) -> str | None:
    for cuisine in sorted(CUISINE_VOCAB, key=len, reverse=True):
        if cuisine in question_lower:
            return cuisine
    return None


def _find_ingredient(question_lower: str, exclude: set[str] = frozenset()) -> str | None:
    for ingredient in sorted(INGREDIENT_VOCAB, key=len, reverse=True):
        if ingredient in question_lower and ingredient not in exclude:
            return ingredient
    return None


def _find_technique(question_lower: str) -> str | None:
    for technique in TECHNIQUE_VOCAB:
        if technique in question_lower:
            return technique
    return None


def detect_shape(question: str) -> ShapeId | None:
    """Classify the question into one of the 15 ShapeId values, or None."""
    q = question.lower().strip()

    if re.search(r"\bbut not\b|\bwithout\b", q):
        return ShapeId.Q14

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

    cuisine = _find_cuisine(q)
    if cuisine and has_ingredient_cue:
        return ShapeId.Q6 if _is_parent_cuisine(cuisine) else ShapeId.Q5

    if cuisine:
        return ShapeId.Q4 if _is_top_level_cuisine(cuisine) else ShapeId.Q3

    if has_ingredient_cue:
        if _find_ingredient(q):
            return ShapeId.Q1

    return None