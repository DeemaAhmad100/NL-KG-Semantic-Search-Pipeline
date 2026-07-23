# Tier 3 — Live-LLM exploration

This tier is the live-LLM exploration of schema-bounded NL→code
generation. It is a first-class M9B deliverable alongside the
deterministic mapper — not a fallback or a bonus. The deterministic
mapper covers the production-discipline arm of the primitive; Tier 3
covers the open-distribution arm.

## What you implement

- `chain.py` — A `GraphCypherQAChain`-style helper that takes a
  question, prepends the schema preamble (`few_shots.SCHEMA_PREAMBLE`)
  and few-shot examples (`few_shots.EXAMPLE_PAIRS`), calls the LLM via
  `llm_client.get_llm_client()`, runs the returned Cypher through
  `allowlist.validate_query_shape()`, and executes the (validated)
  Cypher against the recipe KG.
- `llm_client.py` — Implement the LangChain chain wrapper around the
  resolved provider; the resolution-order dispatch (Ollama → hosted →
  fail-loud) is already wired.

## Course-provided (do not modify)

- `few_shots.py` — schema preamble + 3 example pairs (one with the
  load-bearing `[:SUBCLASS_OF*0..]` traversal).
- `allowlist.py` — `validate_query_shape()` with the triple-stated
  rejection methodology. This is the primary Text2Cypher safety
  surface — Neo4j Community has no per-user RBAC, so the application
  must enforce read-only.
- `mock_llm_cache.json` — used by the CI autograder so Tier 3 tests
  don't require a live LLM call in CI.

## Local setup

```bash
# Install the challenge extras (langchain + ollama + langchain-neo4j)
pip install -r ../requirements-challenge.txt

# Install Ollama:           https://ollama.com
# Then pull the small model used by get_llm_client default:
ollama pull phi3:mini-4k-instruct-q4_K_M

# (If get_llm_client raises OllamaModelMissingError, the message names
# the exact pull command.)
```

If you do not have Ollama locally, set `OPENAI_API_KEY` or
`ANTHROPIC_API_KEY` in `.env` and `get_llm_client()` will fall back to
the hosted provider. The hosted-provider path is OPTIONAL — the
M9B grading does not require paid API access.

## Run the Tier 3 autograder

```bash
pytest tests/test_challenge_tier3.py -v
```

The autograder uses `mock_llm_cache.json` as the LLM stand-in (no live
LLM call), so it runs in CI without paid keys or an Ollama install.
