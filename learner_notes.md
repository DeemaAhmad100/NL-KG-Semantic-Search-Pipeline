# Integration 9B — Learner Notes

Document your design choices and what you learned. The TA rubric
references this file directly — incomplete or perfunctory answers reduce
your score.

## 1. Intents you handled and how you classified them

Describe your `detect_shape` rules. Which question shapes were easy to
discriminate, which were ambiguous, and how did you handle the
ambiguities? Cite at least one specific question from
`data/eval_questions.jsonl` where two shapes were plausible candidates.

> _Your answer here._

## 2. A question that worked end-to-end

Pick one of the 15 canonical questions, walk through the pipeline:
what `detect_shape` returned, what `extract_slots` returned, the
compiled Cypher (with $param placeholders), the bound params dict, and
the rows the driver returned. Paste the actual CLI output.

> _Your answer here._

## 3. A failure mode you diagnosed

Either a question that you initially mis-classified (and why), or an
adversarial / off-template question and what your `UnsupportedQueryError`
message told the caller. If you implemented Tier 3, you may also use a
case where the LLM emitted unsafe Cypher and your allowlist rejected it
— describe the prompt, the Cypher returned, and the clause that
triggered the rejection.

> _Your answer here._

## 4. A design tradeoff between the deterministic mapper and the Tier 3 chain

When would you prefer the deterministic mapper over the LLM chain in
production, and vice versa? Cite a concrete dimension (latency,
auditability, schema-coverage cost, distribution-shift robustness,
operational risk) for each side. Both implementations are first-class —
your answer should reflect that, not pick a winner.

> _Your answer here._
