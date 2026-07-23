"""Shared pytest fixtures for the Integration 9B autograder.

The repo-root sys.path insertion uses `..`, NOT `../starter/` — when
the template is forked the starter/ directory is gone (its contents
become repo root).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from neo4j import GraphDatabase  # noqa: E402


NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "testtest")


@pytest.fixture(scope="session")
def driver():
    """Session-scoped Neo4j driver. The autograder workflow loads the
    fixture via load_fixture.py BEFORE pytest runs, so by the time tests
    execute the graph is populated and the entity_id_unique constraint
    is in place.
    """
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with drv.session() as s:
            s.run("RETURN 1").consume()
        yield drv
    finally:
        drv.close()
