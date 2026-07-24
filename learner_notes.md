# Integration 9B — Learner Notes

Document your design choices and what you learned. The TA rubric
references this file directly — incomplete or perfunctory answers reduce
your score.

## 1. Intents you handled and how you classified them

I classified all 15 shapes using a priority-ordered keyword and regex matching strategy:

**Easy discriminations:**
- Q14 (negation): "but not" / "without" keyword patterns (must check before Q1)
- Q10 (time filter): regex `under (\d+)\s*minutes`
- Q7 (technique): "require" + technique lookup
- Q15 (optional): "optionally tagged with"
- Q11 (inverse): "ingredients used in"
- Q12 (authors): "authors of" + cuisine lookup

**Ambiguous cases:** Q8 vs Q1/Q2. Example: "Find recipes by author Maria Rossi that use basil" is Q8 (conjunction), but "Find recipes that use basil" is Q1, and "Find recipes by author Maria Rossi" is Q2. The discriminator is the co-occurrence of "by ... that use" pattern.

**Key design decision:** I split cuisine classification into two sets:
- `TOP_LEVEL_CUISINES` = {Asian, European, Americas}: triggers hierarchy traversal (Q3→Q4, Q5→Q6)
- `PARENT_CUISINES` = all non-leaf cuisines: only for Q5/Q6 distinction with ingredients

This ensures "Find Italian recipes" → Q3 (direct), while "Find Chinese recipes that use ginger" → Q6 (hierarchy). The rule reflects user expectations: abstract categories like "Asian" imply "all Asian descendants," but specific cuisines like "Italian" mean the specific Italian tag, even though the KG hierarchy has Tuscan/Sicilian as children.

## 2. A question that worked end-to-end

Question: `"Find recipes that use ginger"` (Q1, USES_INGREDIENT)

**Pipeline trace:**
- `detect_shape()` → `ShapeId.Q1` (matched "use" + "ginger" in INGREDIENT_VOCAB)
- `extract_slots()` → `{"ingredient": "ginger"}` (lowercase vocab match, canonicalized)
- `compile_to_cypher()` → template from CANONICAL_CYPHER[Q1]:
  ```
  MATCH (r:Recipe)-[:USES_INGREDIENT]->(:Ingredient {name: $ingredient}) 
  RETURN r.name AS recipe ORDER BY r.name LIMIT 50
  ```
  params: `{"ingredient": "ginger"}`
- Driver executed the parameterized Cypher and returned 22 rows

**CLI output:**
```
$ python cli.py "Find recipes that use ginger"
{'recipe': 'Bao Buns'}
{'recipe': 'Bao Buns #2'}
{'recipe': 'Bibimbap'}
{'recipe': 'Biryani'}
...
{'recipe': 'Vindaloo'}
```

Each row is a dict with the RETURN alias "recipe" as the key. The Neo4j driver handled all parameter binding; no f-string interpolation touched the Cypher.

## 3. A failure mode you diagnosed

Either a question that you initially mis-classified (and why), or an
adversarial / off-template question and what your `UnsupportedQueryError`
message told the caller. If you implemented Tier 3, you may also use a
case where the LLM emitted unsafe Cypher and your allowlist rejected it
— describe the prompt, the Cypher returned, and the clause that
triggered the rejection.



One initial misclassification was treating "Italian" as a parent cuisine (Q4), which caused `detect_shape("Find Italian recipes")` to return Q4 instead of the expected Q3. 

**Diagnosis & Fix:**  
I realized "Italian" is a leaf/specific cuisine in the KG taxonomy (even though it has Tuscan/Sicilian children in some contexts), while "Asian"/"European" are true abstract top-level categories. I updated `TOP_LEVEL_CUISINES` and the classification logic to treat Italian as direct (Q3), which passed the autograder.

**Off-template example:**  
`"Find tomato recipes"` (no "use"/"with" cue) → returns `None` → raises `UnsupportedQueryError` with message listing all 15 supported shapes. This fail-loud behavior is intentional and helps the caller understand how to extend the mapper.

## 4. A design tradeoff between the deterministic mapper and the Tier 3 chain

When would you prefer the deterministic mapper over the LLM chain in
production, and vice versa? Cite a concrete dimension (latency,
auditability, schema-coverage cost, distribution-shift robustness,
operational risk) for each side. Both implementations are first-class —
your answer should reflect that, not pick a winner.


**Prefer deterministic mapper when:**
- **Auditability & Safety** is critical (every Cypher is a static white-box template — no injection risk).
- **Latency & Cost** matter (no LLM call, deterministic O(1) classification).
- Schema is bounded and stable (recipe KG has only 6 labels + 6 relationships).

**Prefer Tier 3 (LLM chain) when:**
- **Distribution-shift robustness** is needed (open-ended user questions that don't fit the 15 shapes).
- Schema evolves frequently (adding new relationship types doesn't require code changes).

The deterministic mapper gives full explainability and zero operational risk on the database, while the LLM chain offers flexibility at the cost of needing strong guardrails (allowlist + schema preamble). In production I would start with the deterministic mapper and gradually add LLM fallback for unsupported queries.