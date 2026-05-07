# Validation Report

## Final local validation update — 2026-05-07

Scope: final local validation only; no new features were added. Validation was run in the local container on Python 3.14.4 with offline/mock paths where possible.

### Status classification

- **Project stage:** experimental MVP / research prototype.
- **Production readiness:** **not production-ready**.
- **Reason for conservative classification:** offline synthetic, mock-ingestion, dashboard payload, package-import, CLI-help, compile, and pytest checks pass locally, but live Google Trends ingestion, prospective real-world validation, calibrated thresholds, full browser automation, deployment rollback evidence, privacy/legal review, and model-risk approval remain unvalidated.

### Passed local checks

- `python -m compileall src scripts tests` completed successfully.
- `pytest` completed successfully: 50 passed.
- `PYTHONPATH=src python - <<'PY' ... import behavioral_stress ... PY` completed successfully.
- CLI help checks completed successfully for ingestion CLI, Google Trends wrapper, dashboard server, dashboard helper, frontend data builder, synthetic demo, and validation runner.
- Mock/offline Google Trends ingestion dry-run completed successfully using a temporary config and temporary output directories.
- Dashboard data build completed successfully to a temporary `dashboard.json` and produced the expected `dashboard.v1` top-level contract keys.
- Frontend/static smoke check completed successfully for required static files, asset references, and basic static-dashboard assumptions.
- `PYTHONPATH=src python scripts/run_validation.py --config <temporary-validation-config>` completed successfully and wrote validation metrics to a temporary output directory.
- `PYTHONPATH=src python scripts/run_synthetic_demo.py --config <temporary-synthetic-config>` completed successfully and wrote synthetic demo artifacts to a temporary output directory.

### Checks that did not pass

- `ruff check` was available but did **not** pass. It reported 120 lint violations, primarily `E501` line-length issues, import-order issues, quoted type annotations, and one unused import. This is a code-quality failure, not an environment limitation.
- A first ad hoc dashboard payload assertion expected outdated keys (`responsible_use`, `series`, `metrics`) and failed. The check was corrected to the current `dashboard.v1` keys (`system`, `bsi`, `posterior`, `alerts`, `top_signals`) and then passed. The failed ad hoc assertion is not treated as a product failure, but it confirms that consumers must use the current dashboard schema.

### Not run / not validated

- Live Google Trends / pytrends ingestion was not run; only offline mock/dry-run ingestion was validated.
- Full browser automation in Chrome or another real browser was not run.
- Networked deployment, Docker runtime, CI pipeline, rollback, monitoring, privacy/legal review, and model-risk approval were not run locally.
- No prospective real-world economic-stress validation or calibrated alert-threshold approval was performed.

### Remaining risks

- Real provider availability, scaling semantics, rate limits, and terms-of-service compliance are unvalidated.
- The BSI and alert reliability/uncertainty fields remain MVP heuristics rather than calibrated scientific confidence intervals.
- Dashboard geography rows are synthetic/demo metadata and should not be interpreted as validated geospatial monitoring.
- Lint debt remains significant because `ruff check` fails.
- Python 3.14.4 local validation is useful but does not replace the declared supported Python 3.10/3.11 compatibility matrix.

### Remaining placeholders / deferred work

- Synthetic-first configs and dashboards remain the validated path.
- Real public-data connectors outside the experimental Google Trends path remain intentionally deferred.
- The Langflow scaffold remains a scaffold/demo path, not a validated orchestration deployment.
- Full BSI design-conformance work remains deferred: local baselines, robust anomalies, calibrated uncertainty, confidence, cross-signal agreement, and alert-threshold approval.
