# System Patterns

## Stable ID Generation
All graph node IDs are content-derived, not sequence-derived:
```python
hashlib.sha256(f"{source}|{source_id}|{version}".encode()).hexdigest()[:16]
```
- `source` examples: `"person"`, `"role"`, `"skill"`, `"chunk"`, `"posting"`
- `version` default: `"v1"` (bump to regenerate IDs intentionally)

## Dual-LLM Pattern
- Claude (`claude-4-5-sonnet-latest`) handles reasoning/extraction intent.
- GPT (`gpt-oss-120b`) handles strict structured JSON via `response_format={"type":"json_schema"}`.
- Genesis-specific constraint: Claude models currently fail on JSON schema response format, so extraction uses GPT path.

## Three-Pillar Scoring
Composite score:
```text
0.4 * skill_score + 0.3 * role_score + 0.3 * experience_score
```
- Skill pillar: exact match weighting (required skills weighted above desired skills), capped at 1.0.
- Role pillar: vector search against role-title embeddings with recency decay.
- Experience pillar: vector search over chunk embeddings, aggregated by candidate.
- Weights are request-configurable.

## Restart-Safe Embed Pipeline
- Embed queries use `WHERE ... embedding IS NULL` to skip already-embedded nodes.
- Batch size `25` with backoff on `429` keeps runs resumable.

## Neo4j CSV Import Pattern (Vagrant primary)
- Host flow:
  1. `python scripts/03_build_graph_csv.py`
  2. `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
- Import script behavior:
  - Stops Neo4j service before admin import.
  - Runs full import from `/workspace/data/exports/graph`.
  - Restarts Neo4j and applies schema/constraints after import.
- Neo4j 5.26 CLI rule:
  - Use positional DB name:
    - `neo4j-admin database import full neo4j --overwrite-destination=true ...`
  - Do not use legacy `--database=neo4j` flag form.

## Corporate TLS Bootstrap Fallback (Provisioning)
Provisioning uses secure-first behavior with explicit fallback:
1. Attempt GPG key retrieval and apt host verification normally.
2. If TLS interception breaks trust chain, retry with bounded fallback (`curl -k`) so VM setup remains operable on work network.
3. Keep fallback isolated to bootstrap surfaces only (do not disable TLS globally in application code).

## FastAPI Lifespan Driver Pattern
- Neo4j driver opens in FastAPI lifespan startup, runs connectivity check, and closes on shutdown.
- Health probe:
```cypher
MATCH (n) RETURN count(n) LIMIT 1
```

## Frontend Typography Pattern
- **No Google Fonts**: `next/font/google` causes hard build failure on corporate network (TLS interception). Use system font stack in `globals.css` instead.
- **System font stack**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- **Minimum readable text**: `text-sm` (14px) for content. Reserve `text-xs` (12px) only for badges/timestamps.
- **Base font size**: `16px` on body (ensures Tailwind rem units compute correctly).
- **Score precision**: `.toFixed(2)` not `.toFixed(3)` — two decimals is scannable, three is noise.

## Windows and Corporate Constraints
- Always set `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` before external HTTPS calls.
- `next/font/google` causes hard build failure — use system font stack or `next/font/local` with bundled fonts.
- Parquet list-like columns may load as `numpy.ndarray`; normalize with `list(...)` before downstream use.
- `.env.*` files are protected by hooks; use approved creation paths and avoid committing secrets.
- Keep O*NET data path resilient with fallback data when external ZIP fetch is unavailable.
