# Fix Plan

Date: 2026-05-07
Purpose: release-readiness cleanup plan for a conservative GitHub-facing merge.

## Goals

1. Keep the project framed as an experimental MVP / research prototype.
2. Make the README accurate, concise, and useful as a GitHub landing page.
3. Remove stale audit contradictions.
4. Fix lint failures without adding product features.
5. Document exactly what is validated and what remains unvalidated.

## Completed fixes

| Area | Completed work |
| --- | --- |
| Ruff/lint | Fixed line-length, import-formatting, quoted-annotation, `zip()` strictness, and unused-import issues; `ruff check` passes locally |
| README | Rewritten around synthetic/offline/mock validation, experimental live ingestion, MVP BSI status, dashboard caveats, and responsible use |
| Audit docs | Replaced stale statements that said ingestion/config tests and ruff were failing; marked those as historical/resolved for offline/mock paths |
| Validation docs | Updated local validation status and unvalidated areas |
| Ingestion wrapper | Added local `src/` path bootstrapping so `python scripts/run_google_trends_ingestion.py ... --dry-run` works from a checkout |
| Release report | Added conservative release-readiness report |

## Current validation expectations

These should pass locally before merge:

```bash
python -m compileall src scripts tests
pytest
ruff check
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
python scripts/run_validation.py --config configs/validation.yaml
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml --dry-run
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
python scripts/healthcheck.py
```

Console scripts should work after successful package installation:

```bash
behavioral-stress-ingest google-trends --config configs/ingestion/google_trends_sample.yaml --dry-run
behavioral-stress-dashboard --host 127.0.0.1 --port 8080 --config configs/production.experimental.yaml
```

## Remaining work not included in this cleanup

- Live Google Trends validation and provider/legal review.
- Real Chrome/browser automation.
- Docker runtime verification.
- Production-grade database-backed alert state.
- Calibrated BSI thresholds and uncertainty.
- Full `BSI_DESIGN.md` implementation.
- Prospective real-world validation.
- Production deployment, rollback, monitoring, and incident playbooks with evidence.

## Guardrails

Do not add recession-prediction claims. Do not claim production readiness. Preserve cautious scientific language and distinguish synthetic/offline validation from live-data validation.
