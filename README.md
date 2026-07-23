# Module 9 Week B — Integration Task: NL → Cypher

Schema-bounded natural-language-to-Cypher generation against the recipe
knowledge graph from the Applied Lab. Two first-class implementations of
the same primitive:

- **Core (`mapper/`)** — a deterministic NL→Cypher mapper over a bounded
  15-template question surface. This is the production-discipline
  implementation when the schema is bounded enough to template: every
  question shape has a hand-authored, parameterized Cypher template; an
  out-of-scope question raises `UnsupportedQueryError` and names the
  supported shapes so the failure is fail-loud and the engineering
  exercise of adding the next template is discoverable.
- **Tier 3 (`challenge/`)** — a `GraphCypherQAChain`-style live-LLM
  implementation of the same primitive, plus a query-shape allowlist
  that rejects any LLM-emitted Cypher carrying destructive clauses.
  This is the live-LLM exploration of the same primitive when the
  input distribution is open.

Both implementations are graded; both are required to demonstrate the
full M9B learning objective. The Tier 3 implementation is opt-in for
the engineering challenge it represents — it is not a backup or a
consolation prize for the core. It is the open-distribution version of
the same NL→code generation primitive.

## What you implement

Core (`mapper/` + `pipeline.py` + `cli.py`):

- `mapper/intent.py` — `detect_shape(question)` returns a `ShapeId`
  from the 15-shape catalog or `None` for out-of-scope.
- `mapper/slots.py` — `extract_slots(question, shape)` fills the
  shape's named slots (ingredient, cuisine, author, technique, etc.)
  from the question text.
- `mapper/compile.py` — `compile_to_cypher(shape, slots)` returns
  `(cypher_string, params_dict)` where the cypher uses `$param`
  parameterization (no f-string interpolation of slot values).
- `pipeline.py` — orchestrate `detect_shape → extract_slots →
  compile_to_cypher → session.run`. Raise `UnsupportedQueryError`
  when `detect_shape` returns `None`.
- `cli.py` — `python cli.py "Find Italian recipes"` pretty-prints
  the top results.

Tier 3 (`challenge/`):

- `challenge/llm_client.py` — `get_llm_client()` resolution chain
  (Ollama → hosted API → fail-loud with install guidance).
- `challenge/chain.py` — build a chain that takes a question, prepends
  the schema preamble + few-shots, calls the LLM for Cypher, validates
  via the allowlist, and runs the Cypher.

Reference materials shipped with this repo (you do not modify):

- `linker/` — bundled reference linker from the Applied Lab (the
  Integration does not redepend on your submitted lab implementation
  so a learner whose lab linker fell short can still complete the
  Integration).
- `mapper/shapes.py` — `ShapeId` enum + the 15 canonical Cypher
  templates (these are the autograder's gold).
- `mapper/errors.py` — `UnsupportedQueryError` with the required
  fail-loud message format.
- `challenge/few_shots.py` — schema preamble + example pairs.
- `challenge/allowlist.py` — `validate_query_shape()` and its
  forbidden-clause set.

## Run locally

```bash
# Bring up Neo4j (uses docker-compose.yml in this repo)
docker compose up -d
# Wait for the "Started." line in the Neo4j logs:
docker compose logs -f neo4j | head

# Install core deps (Tier 3 deps install separately; see challenge/README.md)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Load the fixture and assert acceptance counts
python load_fixture.py

# Run the core autograder
pytest tests/test_mapper.py -v

# Try the CLI on the canonical 15
python cli.py "Find Italian recipes"
```

For Tier 3 setup, see [`challenge/README.md`](challenge/README.md).

## Submitting

See [FORK-SUBMIT.md](FORK-SUBMIT.md) for the fork-and-submit flow.
Both the core mapper tests and the Tier 3 tests must pass in CI.
Document your design decisions in [`learner_notes.md`](learner_notes.md).

---

## License

This repository is provided for educational use only. See [LICENSE](LICENSE) for terms.

You may clone and modify this repository for personal learning and practice, and reference code you wrote here in your professional portfolio. Redistribution outside this course is not permitted.
