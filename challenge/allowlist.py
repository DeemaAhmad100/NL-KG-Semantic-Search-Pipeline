"""Text2Cypher safety allowlist (course-provided; do not modify).

This is the primary Text2Cypher safety surface for Tier 3. Neo4j
Community has no per-user RBAC; a read-only restriction must be
enforced by the application before the driver runs LLM-generated
Cypher.
"""

import re


class UnsupportedCypherError(Exception):
    """Raised when LLM-emitted Cypher contains a forbidden clause."""


# Load-bearing Text2Cypher safety surface (Neo4j Community has no per-user RBAC).
READ_ONLY_CLAUSES = {
    "MATCH", "OPTIONAL", "WHERE", "RETURN", "WITH",
    "ORDER", "LIMIT", "UNION", "SKIP", "AS", "BY", "DISTINCT",
    "AND", "OR", "NOT", "IN", "EXISTS",
}

FORBIDDEN_CLAUSES = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "USING", "FOREACH",
}

_KEYWORD_RE = re.compile(r"\b([A-Z]{3,})\b")

# Strip ' '-quoted, " "-quoted, ` `-quoted string literals and // / /* */ comments
# before keyword extraction so the word "DELETE" inside a string literal does
# not flag the query.
_STRING_LITERAL_RE = re.compile(
    r"'(?:\\.|[^'\\])*'"
    r"|\"(?:\\.|[^\"\\])*\""
    r"|`[^`]*`"
)
_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_strings_and_comments(cypher: str) -> str:
    """Replace string literals and comments with whitespace so the keyword
    scanner sees only structural Cypher tokens.
    """
    cypher = _BLOCK_COMMENT_RE.sub(" ", cypher)
    cypher = _LINE_COMMENT_RE.sub(" ", cypher)
    cypher = _STRING_LITERAL_RE.sub(" ", cypher)
    return cypher


def validate_query_shape(cypher: str) -> None:
    """Raise UnsupportedCypherError if the query contains any forbidden clause.

    Triple-stated methodology (verbatim in integration-task-spec.md, the
    published Integration Guide Tier 3 section, and this docstring):

    - Tokens are extracted as uppercase Cypher keywords (alphabetic, length ≥3).
    - If any token is in FORBIDDEN_CLAUSES → raise immediately, naming the
      offending clause.
    - Comments and string literals are stripped before tokenization to avoid
      flagging the word 'DELETE' inside a quoted name.
    - The allowlist is by-rejection, not by-acceptance: tokens absent from
      both sets (e.g., identifiers, label names) are allowed through; only
      FORBIDDEN_CLAUSES triggers a raise.
    """
    cleaned = _strip_strings_and_comments(cypher)
    for tok in _KEYWORD_RE.findall(cleaned):
        if tok in FORBIDDEN_CLAUSES:
            raise UnsupportedCypherError(
                f"Forbidden clause '{tok}' in LLM-generated Cypher; "
                f"only read clauses permitted."
            )
