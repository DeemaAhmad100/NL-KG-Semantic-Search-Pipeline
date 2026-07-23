"""Linker P/R/F1 scoring (course-provided; do not modify).

Triple-stated methodology (verbatim in lab-spec.md, lab guide page, and
this docstring):

- Predictions are filtered to the gold span set (same doc_id, start, end)
  before scoring; predictions on spans absent from gold are dropped.
- A span is a true positive iff the predicted (node_id, type_label)
  EXACTLY matches gold AND gold is non-NIL.
- A prediction of a wrong (node_id, type_label) on a non-NIL gold is a
  false positive AND a false negative on that span.
- A NIL prediction on a non-NIL gold is a false negative only.
- A non-NIL prediction on a NIL gold is a false positive only.
- A NIL prediction on a NIL gold is a true negative (not counted in
  precision or recall).
- Aggregation is macro-average across documents (per-doc P/R/F1 averaged
  with equal weight per doc; docs with no gold spans are skipped).
"""

from collections import defaultdict
from .types import GoldSpan, LinkResult


def _f1(p: float, r: float) -> float:
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)


def score(predictions: list[LinkResult], gold: list[GoldSpan]) -> dict:
    gold_by_key = {(g.doc_id, g.start, g.end): g for g in gold}
    preds_by_doc: dict[str, list[LinkResult]] = defaultdict(list)
    for p in predictions:
        if (p.doc_id, p.start, p.end) in gold_by_key:
            preds_by_doc[p.doc_id].append(p)

    gold_by_doc: dict[str, list[GoldSpan]] = defaultdict(list)
    for g in gold:
        gold_by_doc[g.doc_id].append(g)

    per_doc_metrics = []
    for doc_id, gold_list in gold_by_doc.items():
        if not gold_list:
            continue
        preds = preds_by_doc.get(doc_id, [])
        pred_by_key = {(pp.doc_id, pp.start, pp.end): pp for pp in preds}

        tp = fp = fn = 0
        for g in gold_list:
            pp = pred_by_key.get((g.doc_id, g.start, g.end))
            if pp is None:
                if g.gold_node_id is not None:
                    fn += 1
                # NIL gold + no prediction → TN (not counted)
                continue
            pred_pair = (pp.predicted_node_id, pp.predicted_type_label)
            gold_pair = (g.gold_node_id, g.gold_type_label)
            if g.gold_node_id is None and pp.predicted_node_id is None:
                continue   # TN
            if g.gold_node_id is None and pp.predicted_node_id is not None:
                fp += 1
                continue
            if g.gold_node_id is not None and pp.predicted_node_id is None:
                fn += 1
                continue
            if pred_pair == gold_pair:
                tp += 1
            else:
                fp += 1
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        per_doc_metrics.append((precision, recall, _f1(precision, recall)))

    if not per_doc_metrics:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    n = len(per_doc_metrics)
    P = sum(m[0] for m in per_doc_metrics) / n
    R = sum(m[1] for m in per_doc_metrics) / n
    F = sum(m[2] for m in per_doc_metrics) / n
    return {"precision": P, "recall": R, "f1": F}
