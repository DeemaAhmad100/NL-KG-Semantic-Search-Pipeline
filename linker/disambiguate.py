"""Candidate disambiguation (course-provided; do not modify).

Signals applied in order:
  1. Resolved-unique — only one candidate; pick it.
  2. Resolved-by-type — NER label maps to exactly one candidate's KG label.
  3. Resolved-by-hierarchy — NER label compatible via [:SUBCLASS_OF*0..]
     traversal to a KG type root.
  4. Resolved-by-context — 1-hop Cypher MATCH from candidate to any
     already-resolved entity in the same document.
  5. NIL — no signal disambiguates, or no candidates returned.
"""

from .types import LinkResult


# Mapping from spaCy/transformer NER label to candidate KG labels.
NER_LABEL_TO_KG_TYPE = {
    "FOOD":     ["Ingredient", "Cuisine"],   # genuinely ambiguous; hierarchy disambiguates
    "DISH":     ["Recipe"],
    "INGREDIENT": ["Ingredient"],
    "CUISINE":  ["Cuisine"],
    "PERSON":   ["Author"],
    "ORG":      ["Author"],                  # cookbook publishers occasionally tagged ORG
    "TECH":     ["Technique"],
    "TECHNIQUE": ["Technique"],
}

# Cuisine-root names — used for hierarchical disambiguation when a FOOD
# surface matches both an :Ingredient and a :Cuisine.
_CUISINE_ROOT_NAMES = {"World", "Asian", "European", "Americas"}


def _is_cuisine_descendant(driver, candidate_id: str) -> bool:
    """True iff candidate is a :Cuisine that reaches a cuisine-root via
    [:SUBCLASS_OF*0..]. The roots themselves count (the *0.. allows it).
    """
    cypher = (
        "MATCH (c:Cuisine {id: $id})-[:SUBCLASS_OF*0..]->(root:Cuisine) "
        "WHERE root.name IN $roots "
        "RETURN count(root) AS c"
    )
    with driver.session() as session:
        rec = session.run(
            cypher, id=candidate_id, roots=list(_CUISINE_ROOT_NAMES)
        ).single()
    return rec is not None and rec["c"] > 0


def _has_context_link(driver, candidate_id: str, neighbor_ids: list[str]) -> bool:
    """True iff candidate has any 1-hop relationship to any neighbor_id."""
    if not neighbor_ids:
        return False
    cypher = (
        "MATCH (c:Entity {id: $id})-[r]-(n:Entity) "
        "WHERE n.id IN $neighbors "
        "RETURN count(r) AS c"
    )
    with driver.session() as session:
        rec = session.run(
            cypher, id=candidate_id, neighbors=neighbor_ids
        ).single()
    return rec is not None and rec["c"] > 0


def disambiguate(
    driver,
    candidates_: list[dict],
    ner_label: str,
    doc_resolved: list[LinkResult],
) -> tuple[dict | None, str]:
    """Return (chosen_candidate_or_None, reason_token).

    See module docstring for the signal cascade.
    """
    if not candidates_:
        return None, "nil-no-candidates"

    # 1. Unique candidate
    if len(candidates_) == 1:
        return candidates_[0], "resolved-unique"

    # 2. Type-filter
    allowed_labels = NER_LABEL_TO_KG_TYPE.get(ner_label, [])
    type_filtered = [
        c for c in candidates_
        if any(lbl in allowed_labels for lbl in c["labels"])
    ]
    if len(type_filtered) == 1:
        return type_filtered[0], "resolved-by-type"

    # 3. Hierarchy-filter — for FOOD/ambiguous: cuisine wins when descendant
    # of a cuisine root. (Bias built in so e.g. "Sichuan" tagged FOOD lands
    # on Cuisine.)
    if type_filtered:
        hierarchy_filtered = []
        for c in type_filtered:
            if "Cuisine" in c["labels"] and _is_cuisine_descendant(driver, c["id"]):
                hierarchy_filtered.append(c)
        if len(hierarchy_filtered) == 1:
            return hierarchy_filtered[0], "resolved-by-hierarchy"
        # If type-filter narrowed to >1 and hierarchy filter doesn't pick
        # exactly one, continue to context.

    # 4. Context: prefer the candidate that has a 1-hop relationship to
    # any already-resolved entity.
    neighbor_ids = [
        r.predicted_node_id for r in doc_resolved
        if r.predicted_node_id is not None
    ]
    pool = type_filtered if type_filtered else candidates_
    context_hits = [
        c for c in pool if _has_context_link(driver, c["id"], neighbor_ids)
    ]
    if len(context_hits) == 1:
        return context_hits[0], "resolved-by-context"

    # 5. NIL — ambiguous after every signal.
    return None, "nil-ambiguous"
