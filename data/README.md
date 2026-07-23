# Data — Integration 9B fixtures

## `recipes_kg.cypher`

The ~200-node recipe knowledge graph from the Applied Lab. Identical
content to the lab fixture — copied (not symlinked) so this repo is
self-contained.

Schema (six labels, six relationship types):

```
:Recipe, :Cuisine, :Ingredient, :Author, :Technique, :Entity (universal id layer)

(:Recipe)-[:USES_INGREDIENT]->(:Ingredient)
(:Recipe)-[:OF_CUISINE]->(:Cuisine)
(:Recipe)-[:BY_AUTHOR]->(:Author)
(:Recipe)-[:REQUIRES_TECHNIQUE]->(:Technique)
(:Cuisine)-[:SUBCLASS_OF]->(:Cuisine)
(:Ingredient)-[:SUBCLASS_OF]->(:Ingredient)
```

Acceptance counts (asserted by `load_fixture.py`, ±2% tolerance):

| Label | Count |
|---|---|
| `:Recipe` | 120 |
| `:Cuisine` | 16 |
| `:Ingredient` | 40 |
| `:Author` | 12 |
| `:Technique` | 12 |
| **Total nodes** | **200** |

| Relationship | Count |
|---|---|
| `:USES_INGREDIENT` | 360 |
| `:OF_CUISINE` | 120 |
| `:BY_AUTHOR` | 120 |
| `:REQUIRES_TECHNIQUE` | 180 |
| `:SUBCLASS_OF` (cuisine) | 15 |
| `:SUBCLASS_OF` (ingredient) | 8 |
| **Total edges** | **803** |

## `eval_questions.jsonl`

The 15 canonical NL questions the deterministic mapper must support,
with their gold shape, slot bindings, and result-set signatures (the
sorted list of recipe names returned by running the canonical Cypher
against this fixture). Used by `tests/test_mapper.py` for end-to-end
equivalence checks and by `tests/test_challenge_tier3.py` for Tier 3
correctness.

## `_build_fixture.py`

Deterministic generator for `recipes_kg.cypher` (seeded random). To
regenerate:

```bash
python data/_build_fixture.py > data/recipes_kg.cypher
```

Do not edit `recipes_kg.cypher` by hand — edit the generator and rerun.
