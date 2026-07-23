"""Tier 3 autograder — mock-LLM-cache path; no live LLM in CI.

Uses challenge/mock_llm_cache.json as the LLM stand-in (the cached
responses are the canonical CANONICAL_CYPHER, so the mock LLM is
"perfect" — Tier 3 autograder is testing the chain plumbing + allowlist,
not LLM quality).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from challenge import chain as chain_mod  # noqa: E402
from challenge import llm_client as llm_mod  # noqa: E402
from challenge.allowlist import (  # noqa: E402
    UnsupportedCypherError,
    validate_query_shape,
)
from mapper import CANONICAL_CYPHER, ShapeId  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
MOCK_CACHE_PATH = REPO_ROOT / "challenge" / "mock_llm_cache.json"
MOCK_CACHE = json.loads(MOCK_CACHE_PATH.read_text())


# --------------------------------------------------------------------------- allowlist

def test_allowlist_passes_read_only_cypher():
    """6 read-only canonical templates pass without raising."""
    read_only_shapes = [
        ShapeId.Q1, ShapeId.Q3, ShapeId.Q7, ShapeId.Q9, ShapeId.Q10, ShapeId.Q15,
    ]
    for shape in read_only_shapes:
        cypher = CANONICAL_CYPHER[shape]
        # Must not raise.
        validate_query_shape(cypher)


@pytest.mark.parametrize("adversarial_cypher,offender", [
    ("MATCH (r:Recipe) DELETE r", "DELETE"),
    ("CREATE (r:Recipe {name: 'pwn'})", "CREATE"),
    ("MERGE (r:Recipe {name: 'pwn'})", "MERGE"),
    ("MATCH (r:Recipe) SET r.name = 'pwn'", "SET"),
    ("DROP CONSTRAINT entity_id_unique", "DROP"),
    ("CALL apoc.export.cypher.all('/tmp/dump.cypher', {})", "CALL"),
])
def test_allowlist_rejects_destructive_clauses(adversarial_cypher, offender):
    """6 adversarial mutations: each must raise UnsupportedCypherError
    naming the offending clause.
    """
    with pytest.raises(UnsupportedCypherError) as exc:
        validate_query_shape(adversarial_cypher)
    assert offender in str(exc.value), (
        f"UnsupportedCypherError message must name the offender {offender}; "
        f"got: {exc.value}"
    )


ADVERSARIAL_PROMPT_CYPHER = [
    ("delete all recipes",          "MATCH (r:Recipe) DETACH DELETE r"),
    ("drop the database",           "DROP DATABASE neo4j"),
    ("set every entity to NIL",     "MATCH (n:Entity) SET n.id = NULL"),
    ("create a backdoor admin",     "CREATE (a:Admin {name: 'pwn'})"),
    ("detach delete recipe 1",      "MATCH (r:Recipe {id: 'recipe:1'}) DETACH DELETE r"),
    ("call apoc.export.cypher",     "CALL apoc.export.cypher.all('/tmp/x', {})"),
]


@pytest.mark.parametrize("prompt,cypher", ADVERSARIAL_PROMPT_CYPHER)
def test_allowlist_rejects_destructive_in_adversarial_prompts(prompt, cypher):
    """If the LLM emitted the destructive Cypher for an adversarial prompt,
    the allowlist must reject it.
    """
    with pytest.raises(UnsupportedCypherError):
        validate_query_shape(cypher)


def test_allowlist_ignores_keywords_in_string_literals():
    """A forbidden keyword inside a string literal must NOT trigger rejection.

    `MATCH (n:Recipe {name: 'DELETE TODO'}) RETURN n` is structurally
    read-only — the DELETE is content, not a clause.
    """
    cypher = "MATCH (n:Recipe {name: 'DELETE TODO'}) RETURN n"
    # Must not raise.
    validate_query_shape(cypher)


# --------------------------------------------------------------------------- chain plumbing

class _MockLLM:
    """A LangChain Runnable-shaped stand-in that returns the cached
    Cypher/params for the question parsed out of the prompt suffix
    "Q: <question>\\nCypher:" line.
    """

    def __init__(self, cache: dict):
        self.cache = cache

    def invoke(self, prompt: str) -> str:
        # Extract last "Q: <text>" segment.
        for line in reversed(prompt.splitlines()):
            line = line.strip()
            if line.startswith("Q:"):
                question = line[2:].strip()
                if question in self.cache:
                    entry = self.cache[question]
                    return (
                        f"Cypher: {entry['cypher']}\n"
                        f"Params: {json.dumps(entry['params'])}"
                    )
                return f"Cypher: \nParams: {{}}"
        return f"Cypher: \nParams: {{}}"


def test_chain_runs_through_mock_llm(driver):
    """Feed 5 questions through chain.run_chain with the mock LLM; verify
    Cypher generated, allowlist passes, query executes, results match
    canonical.
    """
    if not hasattr(chain_mod, "run_chain"):
        pytest.skip("chain.run_chain not yet implemented")

    llm = _MockLLM(MOCK_CACHE)
    sample_questions = [
        ("Find recipes that use ginger",                ShapeId.Q1),
        ("Find Italian recipes",                         ShapeId.Q3),
        ("Find Asian recipes",                           ShapeId.Q4),
        ("Find recipes that use ginger but not garlic",  ShapeId.Q14),
        ("Find recipes optionally tagged with wok technique", ShapeId.Q15),
    ]

    for question, shape in sample_questions:
        try:
            result = chain_mod.run_chain(driver, llm, question)
        except NotImplementedError:
            pytest.skip("chain.run_chain still a TODO")
        assert isinstance(result, dict), "run_chain must return a dict"
        assert result.get("rejected") is False, (
            f"mock LLM cypher must pass the allowlist for {question!r}; "
            f"got rejection_reason={result.get('rejection_reason')}"
        )
        # canonical rows
        cypher = CANONICAL_CYPHER[shape]
        with driver.session() as s:
            gold = [row.data() for row in s.run(cypher, **MOCK_CACHE[question]["params"])]
        if shape in (ShapeId.Q9, ShapeId.Q12):
            assert result["rows"] == gold, f"ranked-shape rows mismatch for {question!r}"
        else:
            assert sorted([tuple(sorted(r.items())) for r in result["rows"]]) == \
                   sorted([tuple(sorted(r.items())) for r in gold]), (
                f"unranked-shape row set mismatch for {question!r}"
            )


# --------------------------------------------------------------------------- llm_client

def test_get_llm_client_model_missing_error():
    """Mock `ollama list` to return empty stdout; assert get_llm_client
    raises OllamaModelMissingError with the exact pull command.
    """
    model = "phi3:mini-4k-instruct-q4_K_M"

    # Force the local-Ollama branch: clear OLLAMA_HOST, OPENAI_API_KEY,
    # ANTHROPIC_API_KEY; pretend ollama binary exists; ollama list returns empty.
    with mock.patch.dict(os.environ, {
        "OLLAMA_HOST": "",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
    }, clear=False):
        # ensure those keys are *absent* (mock.patch.dict with empty string still leaves them set)
        for k in ("OLLAMA_HOST", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            os.environ.pop(k, None)

        with mock.patch.object(llm_mod.shutil, "which", return_value="/usr/local/bin/ollama"), \
             mock.patch.object(llm_mod.subprocess, "run") as mrun:
            mrun.return_value = mock.Mock(stdout="", stderr="", returncode=0)
            with pytest.raises(llm_mod.OllamaModelMissingError) as exc:
                llm_mod.get_llm_client(model=model)
    assert f"ollama pull {model}" in str(exc.value), (
        f"OllamaModelMissingError must name the exact pull command; got: {exc.value}"
    )


# --------------------------------------------------------------------------- triple-stated methodology sentinel

def test_tier3_methodology_docstring_verbatim():
    """Sentinel — the triple-stated Tier 3 scoring methodology must
    appear verbatim in challenge/chain.py module docstring. Catches
    accidental drift.
    """
    src = Path(chain_mod.__file__).read_text()
    required_phrases = [
        "exact-result-set equivalence",
        "deterministic mapper is the gold",
        "row order matters only for the two ranked questions",
        "REPORTED SEPARATELY in the autograder summary",
        "No partial credit on rows",
    ]
    missing = [p for p in required_phrases if p not in src]
    assert not missing, (
        f"chain.py module docstring is missing required verbatim phrases "
        f"from the triple-stated Tier 3 scoring methodology: {missing}"
    )


# --------------------------------------------------------------------------- sentinel

def test_starter_unmodified_fails():
    """Sentinel: an unmodified starter must surface NotImplementedError
    from the Tier 3 TODOs.
    """
    src_files = [
        Path(chain_mod.__file__).read_text(),
        Path(llm_mod.__file__).read_text(),
    ]
    unimpl = sum(s.count('raise NotImplementedError') for s in src_files)
    assert unimpl == 0, (
        f"Sentinel: {unimpl} NotImplementedError sites remain in "
        f"challenge/chain.py + challenge/llm_client.py — implement the "
        f"Tier 3 TODOs before submitting."
    )
