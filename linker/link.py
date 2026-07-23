"""Linker orchestrator (course-provided; do not modify)."""

from .candidates import candidates as _candidates
from .disambiguate import disambiguate
from .types import LinkResult


def link(
    driver,
    doc_id: str,
    text: str,
    ner_spans: list[tuple[int, int, str, str]],
) -> list[LinkResult]:
    """For each NER span, generate candidates and disambiguate to a LinkResult.

    Spans are processed in document order so the doc_resolved context
    window grows monotonically as the linker walks the document.
    """
    # Stable ordering — sort by start offset so context builds left-to-right.
    spans = sorted(ner_spans, key=lambda s: (s[0], s[1]))
    results: list[LinkResult] = []
    for start, end, surface, ner_label in spans:
        cands = _candidates(driver, surface)
        chosen, reason = disambiguate(driver, cands, ner_label, results)
        if chosen is None:
            results.append(LinkResult(
                doc_id=doc_id, start=start, end=end, surface=surface,
                predicted_node_id=None, predicted_type_label=None, reason=reason,
            ))
        else:
            type_label = next(
                (lbl for lbl in chosen["labels"] if lbl != "Entity"),
                None,
            )
            results.append(LinkResult(
                doc_id=doc_id, start=start, end=end, surface=surface,
                predicted_node_id=chosen["id"],
                predicted_type_label=type_label,
                reason=reason,
            ))
    return results
