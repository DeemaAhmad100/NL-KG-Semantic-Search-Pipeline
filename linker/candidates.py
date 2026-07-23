"""Candidate generation against the recipe KG (course-provided; do not modify)."""

_CANDIDATES_CYPHER = (
    "MATCH (n:Entity) "
    "WHERE toLower(n.name) = toLower($surface) "
    "RETURN n.id AS id, n.name AS name, labels(n) AS labels"
)


def candidates(driver, surface: str) -> list[dict]:
    """Return all candidate (:Entity) nodes whose `name` matches `surface`
    case-insensitively.

    Each returned dict has keys:
      - "id": the canonical KG node id (e.g., "ingredient:orange")
      - "name": the node's `name` property
      - "labels": a list of strings, the node's labels EXCLUDING "Entity"

    Uses parameterized Cypher ($surface) — never f-string interpolation.
    """
    out = []
    with driver.session() as session:
        result = session.run(_CANDIDATES_CYPHER, surface=surface)
        for row in result:
            labels = [lbl for lbl in row["labels"] if lbl != "Entity"]
            out.append({"id": row["id"], "name": row["name"], "labels": labels})
    return out
