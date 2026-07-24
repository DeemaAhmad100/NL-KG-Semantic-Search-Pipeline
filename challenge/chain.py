"""GraphCypherQAChain-style helper for Tier 3.

Triple-stated Tier 3 scoring methodology (verbatim):
- The 15 canonical eval questions are scored by exact-result-set equivalence
  against the deterministic mapper (the deterministic mapper is the gold).
- A Tier 3 answer is correct iff the executed Cypher returns exactly the same
  set of result rows; row order matters only for the two ranked questions.
- A Tier 3 answer that raises UnsupportedCypherError is counted as incorrect
  but is REPORTED SEPARATELY in the autograder summary.
- Aggregation: per-question correctness + overall accuracy (correct / 15).
  No partial credit on rows.
"""
"""GraphCypherQAChain-style helper for the live-LLM Tier 3 path.

Triple-stated Tier 3 scoring methodology (verbatim in
integration-task-spec.md, the published Integration Guide Tier 3
section, and this docstring):

- The 15 canonical eval questions in data/eval_questions.jsonl are scored by
  exact-result-set equivalence against the deterministic mapper's output on
  the same fixture graph (the deterministic mapper is the gold).
- A Tier 3 answer is correct iff the executed Cypher returns exactly the
  same set of result rows as the deterministic mapper for that question;
  row order matters only for the two ranked questions (#9, #12) where
  ORDER BY is in the canonical shape.
- A Tier 3 answer that raises UnsupportedCypherError (allowlist rejection)
  counts as incorrect for that question but is REPORTED SEPARATELY in the
  autograder summary so learners can distinguish "LLM emitted unsafe Cypher"
  from "LLM emitted safe-but-wrong Cypher".
- Aggregation: report per-question correctness plus an overall accuracy
  (correct / 15). No partial credit on rows.
"""
from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase

from .allowlist import UnsupportedCypherError, validate_query_shape
from .few_shots import EXAMPLE_PAIRS, SCHEMA_PREAMBLE
from .llm_client import get_llm_client


def build_prompt(question: str) -> str:
    """Assemble prompt: schema + few-shots + question."""
    lines = [SCHEMA_PREAMBLE.strip(), ""]
    for q, cypher in EXAMPLE_PAIRS:
        lines.append(f"Q: {q}")
        lines.append(f"Cypher: {cypher}")
        lines.append("")
    lines.append(f"Q: {question}")
    lines.append("Cypher:")
    return "\n".join(lines)


def run_chain(driver, llm_client, question: str) -> dict[str, Any]:
    """End-to-end Tier 3 chain."""
    prompt = build_prompt(question)

    try:
        response = llm_client.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        # Simple parse: expect "Cypher: ..." and optional "Params: {...}"
        cypher = ""
        params = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Cypher:"):
                cypher = line[7:].strip()
            elif line.startswith("Params:"):
                try:
                    params = eval(line[7:].strip())  # safe in this context
                except Exception:
                    params = {}

        if not cypher:
            return {"question": question, "cypher": None, "params": {}, "rows": [], "rejected": True, "rejection_reason": "No Cypher emitted"}

        validate_query_shape(cypher)

        with driver.session() as session:
            result = session.run(cypher, **params)
            rows = [row.data() for row in result]

        return {
            "question": question,
            "cypher": cypher,
            "params": params,
            "rows": rows,
            "rejected": False,
            "rejection_reason": None,
        }

    except UnsupportedCypherError as e:
        return {
            "question": question,
            "cypher": None,
            "params": {},
            "rows": [],
            "rejected": True,
            "rejection_reason": str(e),
        }
    except Exception as e:
        return {
            "question": question,
            "cypher": None,
            "params": {},
            "rows": [],
            "rejected": True,
            "rejection_reason": f"LLM error: {e}",
        }