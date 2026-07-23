"""Schema preamble + few-shot example pairs (course-provided; do not modify).

These are prepended to every LLM call. They constrain the LLM to the
recipe-KG vocabulary and remind it to use parameterized Cypher and the
[:SUBCLASS_OF*0..] traversal idiom.
"""

SCHEMA_PREAMBLE = """
This is a Neo4j property-graph schema. Use only these labels and
relationships.

Labels: Recipe, Cuisine, Ingredient, Author, Technique. Every node also
carries :Entity for uniqueness.

Relationships:
  (:Recipe)-[:USES_INGREDIENT]->(:Ingredient)
  (:Recipe)-[:OF_CUISINE]->(:Cuisine)
  (:Recipe)-[:BY_AUTHOR]->(:Author)
  (:Recipe)-[:REQUIRES_TECHNIQUE]->(:Technique)
  (:Cuisine)-[:SUBCLASS_OF]->(:Cuisine)
  (:Ingredient)-[:SUBCLASS_OF]->(:Ingredient)

Always use parameterized Cypher with $param syntax. Read-only clauses only
(MATCH, OPTIONAL MATCH, WHERE, RETURN, WITH, ORDER BY, LIMIT, UNION).

When a question names a cuisine or ingredient category that has subtypes,
include [:SUBCLASS_OF*0..] in the path so the answer covers descendants.
""".strip()


EXAMPLE_PAIRS = [
    {
        "q": "Find Asian recipes",
        "cypher": (
            "MATCH (r:Recipe)-[:OF_CUISINE]->(c:Cuisine) "
            "MATCH (c)-[:SUBCLASS_OF*0..]->(:Cuisine {name: $cuisine}) "
            "RETURN r.name AS recipe LIMIT 25"
        ),
        "params": {"cuisine": "Asian"},
    },
    {
        "q": "Find recipes that use ginger",
        "cypher": (
            "MATCH (r:Recipe)-[:USES_INGREDIENT]->(:Ingredient {name: $ingredient}) "
            "RETURN r.name AS recipe LIMIT 25"
        ),
        "params": {"ingredient": "ginger"},
    },
    {
        "q": "Find Sichuan recipes that use ginger",
        "cypher": (
            "MATCH (r:Recipe)-[:OF_CUISINE]->(c:Cuisine) "
            "MATCH (c)-[:SUBCLASS_OF*0..]->(:Cuisine {name: $cuisine}) "
            "MATCH (r)-[:USES_INGREDIENT]->(:Ingredient {name: $ingredient}) "
            "RETURN r.name AS recipe LIMIT 25"
        ),
        "params": {"cuisine": "Sichuan", "ingredient": "ginger"},
    },
]
