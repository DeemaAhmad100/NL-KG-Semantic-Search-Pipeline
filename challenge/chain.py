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

from .allowlist import UnsupportedCypherError, validate_query_shape
from .few_shots import EXAMPLE_PAIRS, SCHEMA_PREAMBLE


# Graceful import — langchain_neo4j is optional (not installed in CI).
# When unavailable, set the symbol to None and let callers decide whether
# to skip with a clear reason or use a fake.
try:
    from langchain_neo4j import GraphCypherQAChain  # type: ignore
    LANGCHAIN_AVAILABLE = True
except ImportError:
    GraphCypherQAChain = None  # type: ignore
    LANGCHAIN_AVAILABLE = False


def build_prompt(question: str) -> str:
    """Compose the LLM prompt: schema preamble + few-shots + question.

    Course-helper stub. The exact prompt format is up to you, but at
    minimum:
      - Start with SCHEMA_PREAMBLE.
      - Append each EXAMPLE_PAIRS entry as "Q: ...\\nCypher: ...".
      - End with "Q: {question}\\nCypher:" so the LLM continues with Cypher.
    """
    # TODO: assemble the prompt string from SCHEMA_PREAMBLE + EXAMPLE_PAIRS + question.
    raise NotImplementedError(
        "build_prompt is not yet implemented — see the Integration Guide "
        "Tier 3 prompt section."
    )


def run_chain(driver, llm_client, question: str) -> dict[str, Any]:
    """Run one question through the chain end-to-end.

    Returns a dict with keys:
      - "question": the input question
      - "cypher":   the LLM-emitted Cypher string (or None if the LLM
                    refused / returned empty)
      - "params":   the params dict the LLM emitted (or {} if none)
      - "rows":     list of result rows from session.run (or [] if
                    the allowlist rejected the Cypher)
      - "rejected": True iff the allowlist raised; False otherwise
      - "rejection_reason": the UnsupportedCypherError message, or None

    Required behaviour:
      1. Build the prompt via build_prompt(question).
      2. Invoke the LLM (llm_client.invoke(prompt) — LangChain Runnable
         convention).
      3. Parse the LLM response to extract a Cypher string and a params
         dict. (The few-shot format is "Cypher: ...\\nParams: {...}".)
      4. Call validate_query_shape(cypher). Catch UnsupportedCypherError
         and return a dict with rejected=True.
      5. If validation passed, run the Cypher via session.run(cypher,
         **params) and return the rows.
    """
    # TODO: orchestrate prompt → LLM → parse → allowlist → execute.
    raise NotImplementedError(
        "run_chain is not yet implemented — see the Integration Guide "
        "Tier 3 orchestration section."
    )
