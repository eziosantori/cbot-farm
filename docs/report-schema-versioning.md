# Report Schema Versioning

## Goal
Keep report readers stable even when legacy artifacts remain on disk and newer runs/manifests are produced with richer metadata.

## Scope
- Run reports (`run_*.json`)
- Ingest manifests (`reports/ingest/manifest_*.json`)

## Current Versions
- Run reports: `schema_version = 2`
- Ingest manifests: `schema_version = 2`

## Canonical Fields

### Run report
- `schema_version`
- `report_kind = "run_report"`
- `created_at`
- `run_at`
- `strategy`
- `strategy_id`
- `market`
- `symbol`
- `timeframes`
- `target`
- `metrics`
- `status`

### Ingest manifest
- `schema_version`
- `report_kind = "ingest_manifest"`
- `created_at`
- `provider`
- `status`
- `from`
- `to`
- `summary`
- `filters`
- `results`

## Migration Strategy
- New writers emit the current schema directly.
- Readers/indexers normalize legacy payloads through `cbot_farm/report_schema.py`.
- Migration is non-destructive at read time.
- Optional in-place rewrite is available with:

```bash
pnpm run reports:migrate
```

## Design Rule
- Business logic should consume normalized payloads.
- Legacy branching should live in the schema migration layer, not in page logic, API handlers, or analytics code.
