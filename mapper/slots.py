"""Slot extraction — fill the named slots a shape's Cypher template needs.

Each shape in `shapes.CANONICAL_CYPHER` carries `$param` placeholders.
Your `extract_slots(question, shape)` returns a dict whose keys are the
parameter names the template expects, e.g.:

  ShapeId.Q1 → {"ingredient": "ginger"}
  ShapeId.Q5 → {"cuisine": "Sichuan", "ingredient": "ginger"}
  ShapeId.Q9 → {"cuisine": "Italian"}
  ShapeId.Q10 → {"max_minutes": 30}
  ShapeId.Q14 → {"ingredient": "ginger", "exclude_ingredient": "garlic"}

See `data/eval_questions.jsonl` for the gold (question_text, shape, slots)
triples used by the autograder.
"""

import re
import spacy

from .shapes import ShapeId
from .intent import (
    CUISINE_VOCAB, INGREDIENT_VOCAB, TECHNIQUE_VOCAB,
    _find_cuisine, _find_ingredient, _find_technique
)

# Load spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not installed, we'll get an error later
    nlp = None


# Mapping from lowercase ingredient names to canonical forms
INGREDIENT_CANONICAL = {ing.lower(): ing for ing in INGREDIENT_VOCAB}

# Mapping from lowercase cuisine names to canonical forms
CUISINE_CANONICAL = {cui.lower(): cui for cui in CUISINE_VOCAB}

# Mapping from lowercase technique names to canonical forms
TECHNIQUE_CANONICAL = {tech.lower(): tech for tech in TECHNIQUE_VOCAB}

# Known authors in canonical form (from the KG)
AUTHOR_CANONICAL_MAP = {
    "maria rossi": "Maria Rossi",
    "giovanni ferri": "Giovanni Ferri",
    "chen wei": "Chen Wei",
    "li mei": "Li Mei",
    "hiro tanaka": "Hiro Tanaka",
    "priya sharma": "Priya Sharma",
    "somchai phan": "Somchai Phan",
    "pierre dubois": "Pierre Dubois",
    "carmen lopez": "Carmen Lopez",
    "diego hernandez": "Diego Hernandez",
    "basil roy": "Basil Roy",
    "sage lindholm": "Sage Lindholm",
}


def _extract_author(question: str) -> str | None:
    """Extract author name using spaCy NER, fallback to keyword matching."""
    # Try spaCy NER first
    if nlp:
        doc = nlp(question)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check if this matches any known author (case-insensitive)
                ent_text_lower = ent.text.lower()
                for known_author_lower, known_author_canonical in AUTHOR_CANONICAL_MAP.items():
                    if known_author_lower in ent_text_lower or ent_text_lower in known_author_lower:
                        return known_author_canonical
                # If not in canonical map, try direct match
                return ent.text
    
    # Fallback: try to match against known authors
    question_lower = question.lower()
    for known_author_lower, known_author_canonical in AUTHOR_CANONICAL_MAP.items():
        if known_author_lower in question_lower:
            return known_author_canonical
    
    return None


def _extract_canonical_ingredient(question: str) -> str | None:
    """Extract ingredient and return canonical form."""
    ingredient = _find_ingredient(question.lower())
    if ingredient:
        return ingredient.capitalize() if ingredient not in INGREDIENT_CANONICAL else ingredient
    return None


def _extract_canonical_cuisine(question: str) -> str | None:
    """Extract cuisine and return canonical form."""
    cuisine = _find_cuisine(question.lower())
    if cuisine:
        # Map to canonical form (first letter capitalized)
        if cuisine == "northamerican":
            return "NorthAmerican"
        else:
            return cuisine.capitalize()
    return None


def _extract_canonical_technique(question: str) -> str | None:
    """Extract technique and return canonical form."""
    technique = _find_technique(question.lower())
    if technique:
        return technique.lower()
    return None


def extract_slots(question: str, shape: ShapeId) -> dict:
    """Extract slot values for the given shape from the question text.

    Return a dict whose keys EXACTLY match the `$param` names in
    shapes.CANONICAL_CYPHER[shape]. Values must be in canonical form.
    """
    slots = {}
    question_lower = question.lower()
    
    if shape == ShapeId.Q1:
        # "Find recipes that use ginger" → {"ingredient": "ginger"}
        ingredient = _extract_canonical_ingredient(question)
        if ingredient:
            slots["ingredient"] = ingredient
    
    elif shape == ShapeId.Q2:
        # "Find recipes by author Maria Rossi" → {"author": "Maria Rossi"}
        author = _extract_author(question)
        if author:
            slots["author"] = author
    
    elif shape == ShapeId.Q3:
        # "Find Italian recipes" → {"cuisine": "Italian"}
        cuisine = _extract_canonical_cuisine(question)
        if cuisine:
            slots["cuisine"] = cuisine
    
    elif shape == ShapeId.Q4:
        # "Find Asian recipes" → {"cuisine": "Asian"}
        cuisine = _extract_canonical_cuisine(question)
        if cuisine:
            slots["cuisine"] = cuisine
    
    elif shape == ShapeId.Q5:
        # "Find Sichuan recipes that use ginger" → {"cuisine": "Sichuan", "ingredient": "ginger"}
        cuisine = _extract_canonical_cuisine(question)
        ingredient = _extract_canonical_ingredient(question)
        if cuisine:
            slots["cuisine"] = cuisine
        if ingredient:
            slots["ingredient"] = ingredient
    
    elif shape == ShapeId.Q6:
        # "Find Chinese recipes that use ginger" → {"cuisine": "Chinese", "ingredient": "ginger"}
        cuisine = _extract_canonical_cuisine(question)
        ingredient = _extract_canonical_ingredient(question)
        if cuisine:
            slots["cuisine"] = cuisine
        if ingredient:
            slots["ingredient"] = ingredient
    
    elif shape == ShapeId.Q7:
        # "Find recipes that require wok technique" → {"technique": "wok"}
        technique = _extract_canonical_technique(question)
        if technique:
            slots["technique"] = technique
    
    elif shape == ShapeId.Q8:
        # "Find recipes by author Maria Rossi that use basil" → {"author": "Maria Rossi", "ingredient": "basil"}
        author = _extract_author(question)
        ingredient = _extract_canonical_ingredient(question)
        if author:
            slots["author"] = author
        if ingredient:
            slots["ingredient"] = ingredient
    
    elif shape == ShapeId.Q9:
        # "Find Italian recipes ranked by popularity" → {"cuisine": "Italian"}
        cuisine = _extract_canonical_cuisine(question)
        if cuisine:
            slots["cuisine"] = cuisine
    
    elif shape == ShapeId.Q10:
        # "Find recipes with prep time under 30 minutes" → {"max_minutes": 30}
        match = re.search(r"under\s+(\d+)\s*minutes", question_lower)
        if match:
            slots["max_minutes"] = int(match.group(1))
    
    elif shape == ShapeId.Q11:
        # "Find ingredients used in Italian recipes" → {"cuisine": "Italian"}
        cuisine = _extract_canonical_cuisine(question)
        if cuisine:
            slots["cuisine"] = cuisine
    
    elif shape == ShapeId.Q12:
        # "Find authors of Sichuan recipes" → {"cuisine": "Sichuan"}
        cuisine = _extract_canonical_cuisine(question)
        if cuisine:
            slots["cuisine"] = cuisine
    
    elif shape == ShapeId.Q13:
        # "Find recipes that use peppercorn or any subtype" → {"ingredient": "peppercorn"}
        ingredient = _extract_canonical_ingredient(question)
        if ingredient:
            slots["ingredient"] = ingredient
    
    elif shape == ShapeId.Q14:
        # "Find recipes that use ginger but not garlic" → {"ingredient": "ginger", "exclude_ingredient": "garlic"}
        if "but not" in question_lower:
            parts = question_lower.split("but not")
        else:
            parts = question_lower.split("without")
        
        # Find positive ingredient in first part
        ingredient = _find_ingredient(parts[0])
        if ingredient:
            slots["ingredient"] = ingredient.capitalize() if ingredient not in INGREDIENT_CANONICAL else ingredient
        
        # Find negative ingredient in second part
        if len(parts) > 1:
            exclude_ingredient = _find_ingredient(parts[1])
            if exclude_ingredient:
                slots["exclude_ingredient"] = exclude_ingredient.capitalize() if exclude_ingredient not in INGREDIENT_CANONICAL else exclude_ingredient
    
    elif shape == ShapeId.Q15:
        # "Find recipes optionally tagged with wok technique" → {"technique": "wok"}
        technique = _extract_canonical_technique(question)
        if technique:
            slots["technique"] = technique
    
    return slots

