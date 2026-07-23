# Module 9 Week B — Integration Task — Fork-and-Submit Flow

All Module 9 assignments use a fork-and-submit flow instead of GitHub
Classroom. GitHub is sunsetting Classroom (full transition 2026-08-28);
M8 and M9 are on the fork-and-submit replacement.

## 5 steps

1. **Fork this repo** (button top-right) → owner = your personal GitHub
   account → Create fork.
2. **Enable Actions on your fork.** Actions tab → click *"I understand my
   workflows, go ahead and enable them"*. One-time per fork; the autograder
   cannot run on your PR until this is done.
3. **Clone your fork** (not this repo):
   `git clone https://github.com/<you>/m9-i9b.git`
4. **Branch, implement, commit, push:**
   ```bash
   git checkout -b integration-9b-nl-cypher
   # edit the files (see the Integration Task guide for the deliverables)
   git add .
   git commit -m "integration-9b: implementation"
   git push origin integration-9b-nl-cypher
   ```
5. **Open a PR *within your fork*** — base `main`, compare `integration-9b-nl-cypher`,
   **base repository = your fork** (GitHub defaults to upstream — change it).
   When CI passes, paste the PR URL into
   TalentLMS → Module 9 Week B → Integration Task.

## Common failure modes

- **PR opened against upstream `LevelUp-Applied-AI/m9-i9b` instead of your fork.**
  GitHub disables Actions secrets and downgrades the workflow token for
  cross-fork PRs, and TAs will see your work in a flood of cross-cohort
  PRs to the template. Always change the base-repository dropdown to your
  own fork.
- **Actions disabled on the fork.** No green or red CI check on the PR.
  Re-do Setup step 2, then push an empty commit to retrigger:
  `git commit --allow-empty -m "ci: trigger" && git push`.
- **Forgot to start Neo4j locally before running `pytest tests/ -v`.**
  Local tests fail but CI is fine — the autograder workflow brings up its
  own Neo4j service container. For local runs:
  `docker compose up -d && docker compose logs -f neo4j | head` and wait
  for the "Started." line before invoking pytest.
