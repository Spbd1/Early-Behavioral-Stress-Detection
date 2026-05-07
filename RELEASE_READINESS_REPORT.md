# Release Readiness Report

Date: 2026-05-07
Scope: final local cleanup and validation for a GitHub-facing merge.

## 1. What was fixed

- Fixed ruff/lint failures without adding product features.
- Added `src/` path bootstrapping to the Google Trends ingestion wrapper script so the documented direct script command works from a checkout.
- Rewrote stale audit/planning/tracker documents to remove contradictions about ingestion tests, config parsing, and lint status.
- Preserved cautious scientific language and explicit not-production/not-recession-prediction guardrails.

## 2. README improvements

- Rebuilt README as a GitHub landing page with a visible status box.
- Moved quick-start and safety caveats near the top.
- Added `[ingestion]` to optional extras.
- Distinguished validated synthetic/offline/mock paths from experimental live Google Trends ingestion.
- Clarified that the browser dashboard is Chrome-friendly but synthetic/demo-oriented.
- Clarified that the BSI is an MVP heuristic implementation, not the full `BSI_DESIGN.md` specification.
- Corrected alert-history wording: MVP JSONL persistent alert history exists; production-grade database-backed/replayable alert state is still deferred.
- Added a current validation snapshot and explicit limitations/responsible-use section.

## 3. Lint status

`ruff check` passes locally.

Historical lint debt was resolved, including line-length issues, import formatting, quoted type annotations, `zip()` strictness warnings, and an unused import.

## 4. Test status

`pytest` passes locally with 50 tests.

The test suite covers synthetic workflow behavior, data validation, Google Trends dry-run/offline ingestion behavior, MVP BSI contracts, geo alerting, dashboard schema/static assumptions, frontend static assets, keyword generation, signal retirement, and operations hardening checks.

## 5. Commands run

```bash
python -m compileall src scripts tests
pytest
ruff check
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
python scripts/run_validation.py --config configs/validation.yaml
PYTHONPATH=src python -m behavioral_stress.ingestion.cli google-trends --config configs/ingestion/google_trends_sample.yaml --dry-run
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml --dry-run
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
python scripts/healthcheck.py
timeout 2s python -m http.server 8080 --directory frontend
```

Additional command-accuracy checks:

- `behavioral-stress-ingest` and `behavioral-stress-dashboard` are declared console scripts in `pyproject.toml`.
- Direct execution of those console scripts could not be validated in this container because editable installation could not complete: build dependencies could not be fetched and `setuptools.build_meta` was unavailable.

## 6. What remains unvalidated

- Live Google Trends / pytrends ingestion.
- Google provider scaling stability, rate limits, regional coverage, and legal/terms review.
- Real Chrome/browser automation.
- Docker runtime.
- Networked deployment, rollback, monitoring integrations, and incident ownership.
- Privacy/legal review and model-risk approval.
- Prospective real-world validation and calibrated BSI/alert thresholds.
- Full production-grade database-backed alert audit/replay state.

## 7. Remaining risks

- Synthetic/offline/mock validation does not prove real-world predictive performance.
- MVP BSI reliability and uncertainty fields are heuristic labels, not calibrated confidence intervals.
- Cross-geography comparisons can be misleading without local baselines, sample-size review, and provider coverage review.
- Live data providers can change formats, sampling, scaling, throttling, or availability.
- The project still needs stronger deployment and browser evidence before any operational claim.

## 8. Final classification

- **Experimental MVP / research prototype.**
- **Not production-ready.**
- **Not a recession predictor.**
