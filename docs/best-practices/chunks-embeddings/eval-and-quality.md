# Retrieval Evaluation and Quality

## Core Metrics
- `Recall@k`: whether relevant chunks are retrieved.
- `MRR`: ranking quality.
- `Groundedness`: generated answer is supported by cited chunks.
- `Citation precision`: cited chunks truly support answer claims.

## Evaluation Set
- Build small labeled query set for skills/roles/postings scenarios.
- Track expected entities and supporting document IDs.

## Drift Checks
- Monitor embedding cosine distribution shifts.
- Track hit-rate deltas after model/version updates.
- Compare hybrid retrieval vs vector-only baseline weekly or per release.

## Inference
- Inference: metric thresholds are domain-dependent; set initial SLOs from baseline runs and tighten iteratively.
