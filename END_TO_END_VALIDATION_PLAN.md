# End-to-End Validation Plan

Date: 2026-05-07
Scope: conservative validation plan for the experimental MVP / research prototype.

## Validation tiers

| Tier | Purpose | Current status |
| --- | --- | --- |
| Tier 0: static/code quality | Compile and lint source, scripts, and tests | Passing locally |
| Tier 1: unit/smoke tests | Exercise synthetic workflow, ingestion dry-run, BSI, alerting, dashboard schema, and safety guardrails | Passing locally |
| Tier 2: synthetic end-to-end | Run synthetic demo and validation configs with known latent states | Passing locally |
| Tier 3: offline/mock ingestion | Run deterministic Google Trends dry-run without network/pytrends | Passing locally |
| Tier 4: dashboard payload/static smoke | Build `frontend/dashboard.json` and serve static assets | Payload build passes; real browser automation not run |
| Tier 5: live provider validation | Validate pytrends/live Google Trends behavior under legal/provider constraints | Not validated |
| Tier 6: deployment/runtime | Validate Docker, hosted runtime, rollback, monitoring, incident response | Not validated |
| Tier 7: scientific/operational approval | Prospective real-world validation, calibrated thresholds, model-risk review | Not validated |

## Required local release checks

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

## Browser/dashboard checks

Minimum local non-browser check:

```bash
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
python -m http.server 8080 --directory frontend
```

A future browser-validation tier should open Chrome against `http://127.0.0.1:8080`, verify the experimental/not-recession-prediction labels are visible, and check charts/tables/report export with generated synthetic data. That tier has not been run locally.

## Live ingestion validation requirements before any claim

Do not claim live Google Trends validation until there is evidence for:

- pytrends/provider behavior under the intended environment.
- Rate limits, retries, backoff, and failure handling.
- Provider terms/legal approval.
- Geography-code support for intended regions.
- Replay from immutable raw artifacts.
- Stability review for Google Trends sampling/scaling.

## Production-readiness requirements before any operational claim

Do not claim production readiness until there is evidence for:

- Docker/runtime execution and health checks in the target environment.
- Database-backed alert/audit state with replay and retention policy.
- Monitoring, rollback, on-call ownership, and incident playbooks tested in practice.
- Privacy/legal/model-risk approval.
- Prospective real-world validation and calibrated alert thresholds.

## Final validation interpretation

Passing local checks supports only the synthetic/offline/mock research-demo path. It does not validate live data, real-world predictive performance, causal interpretation, or production operation.
