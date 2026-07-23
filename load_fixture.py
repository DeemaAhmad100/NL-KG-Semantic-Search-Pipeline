"""Load the Integration 9B recipe KG fixture into Neo4j and assert acceptance.

Run order:
    1. Apply the entity_id_unique constraint (M9B Identity Discipline).
    2. Execute data/recipes_kg.cypher (the canonical ~200-node recipe graph).
    3. Assert per-label node counts and total edge counts (±2% tolerance per
       the canonical fixture-size targets).
    4. Assert no duplicate :Entity.id (Identity Discipline holds).
    5. Exit non-zero on any mismatch.

Env vars (with defaults for local docker-compose):
    NEO4J_URI       bolt://localhost:7687
    NEO4J_USER      neo4j
    NEO4J_PASSWORD  testtest
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "testtest")

DATA_DIR = Path(__file__).parent / "data"
RECIPES_CYPHER = DATA_DIR / "recipes_kg.cypher"

# Acceptance expectations (kept in lockstep with the generator).
EXPECTED_LABEL_COUNTS = {
    "Recipe": 120,
    "Cuisine": 16,
    "Ingredient": 40,
    "Author": 12,
    "Technique": 12,
}
EXPECTED_TOTAL_NODES = 200

EXPECTED_REL_COUNTS = {
    "USES_INGREDIENT": 360,
    "OF_CUISINE": 120,
    "BY_AUTHOR": 120,
    "REQUIRES_TECHNIQUE": 180,
    # SUBCLASS_OF is the union of cuisine (15) + ingredient (8) chains.
    "SUBCLASS_OF": 23,
}
EXPECTED_TOTAL_RELS = sum(EXPECTED_REL_COUNTS.values())  # 803

TOLERANCE = 0.02  # ±2%

CONSTRAINT_CYPHER = (
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
    "FOR (n:Entity) REQUIRE n.id IS UNIQUE"
)

DUP_DETECT_CYPHER = (
    "MATCH (n:Entity) "
    "WITH n.id AS id, count(*) AS c "
    "WHERE c > 1 "
    "RETURN id, c"
)

_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"//[^\n]*")


def _split_statements(text: str) -> list[str]:
    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _LINE_COMMENT_RE.sub("", text)
    return [s.strip() for s in text.split(";") if s.strip()]


def _run_cypher_file(session, path: Path) -> None:
    for stmt in _split_statements(path.read_text()):
        session.run(stmt).consume()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"ACCEPTANCE FAILURE: {message}", file=sys.stderr)
        sys.exit(1)


def _within_tolerance(actual: int, expected: int) -> bool:
    if expected == 0:
        return actual == 0
    return abs(actual - expected) / expected <= TOLERANCE


def main() -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run(CONSTRAINT_CYPHER).consume()
            _run_cypher_file(session, RECIPES_CYPHER)

            for label, expected in EXPECTED_LABEL_COUNTS.items():
                actual = session.run(
                    f"MATCH (n:`{label}`) RETURN count(n) AS c"
                ).single()["c"]
                _assert(
                    _within_tolerance(actual, expected),
                    f"label :{label} expected ~{expected} (±2%), got {actual}",
                )

            total_nodes = session.run(
                "MATCH (n) RETURN count(n) AS c"
            ).single()["c"]
            _assert(
                _within_tolerance(total_nodes, EXPECTED_TOTAL_NODES),
                f"total nodes expected ~{EXPECTED_TOTAL_NODES} (±2%), got {total_nodes}",
            )

            for rel, expected in EXPECTED_REL_COUNTS.items():
                actual = session.run(
                    f"MATCH ()-[r:`{rel}`]->() RETURN count(r) AS c"
                ).single()["c"]
                _assert(
                    _within_tolerance(actual, expected),
                    f"relationship :{rel} expected ~{expected} (±2%), got {actual}",
                )

            total_rels = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            ).single()["c"]
            _assert(
                _within_tolerance(total_rels, EXPECTED_TOTAL_RELS),
                f"total relationships expected ~{EXPECTED_TOTAL_RELS} (±2%), got {total_rels}",
            )

            dup_rows = list(session.run(DUP_DETECT_CYPHER))
            _assert(
                not dup_rows,
                f"Identity Discipline VIOLATED — duplicate :Entity.id rows: {dup_rows}",
            )

            print(
                f"Fixture loaded: {total_nodes} nodes, {total_rels} relationships. "
                f"Entity-id uniqueness OK."
            )
    finally:
        driver.close()


if __name__ == "__main__":
    main()
