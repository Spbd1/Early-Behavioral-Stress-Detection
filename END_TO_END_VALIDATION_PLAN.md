# End-to-End Validation Plan

Source audit: `CURRENT_STATE_AUDIT.md` dated 2026-05-07. This plan defines the minimal validation path requested for the current repository state. It does not implement fixes.

## Goal

Validate that the repository can produce one coherent offline artifact chain:

```text
synthetic observations
-> HMM/posterior or mocked posterior
-> BSI
-> alert decision
-> report output
-> dashboard JSON payload
-> frontend/static smoke test
```

The purpose is correctness, observability, and reproducibility. This is not a production-readiness test and not evidence of real-world predictive validity.

## Constraints

- Must run without network access by default.
- Must not require external credentials.
- Must use deterministic synthetic data or deterministic mocked posterior values.
- Must preserve current architecture and add only thin adapters/tests when implemented later.
- Must clearly label outputs as `synthetic_only` or `demo` until live validation exists.
- Must fail on schema drift between backend payloads and frontend expectations.

## Implementation update — 2026-05-07

The first offline smoke path is now implemented in `tests/test_alert_persistence_and_smoke.py`. It uses synthetic/mocked observations only and validates:

1. MVP BSI computation through `GeoAwareAlertEngine.evaluate`.
2. Alert decision generation with suppressions/warnings preserved.
3. Conservative report generation with safe wording.
4. Dashboard-ready JSON payload serialization via `GeoAwareAlertEngine.dashboard_payload`.
5. No live Google Trends, API keys, or network access.

The same test module also covers JSONL alert persistence/replay and geo-safety warning/suppression behavior for low-confidence city/metro and unsupported geographies. Google Trends ingestion and frontend architecture are intentionally unchanged.

## Minimal validation path overview

| Stage | Input | Output | Primary validation |
|---|---|---|---|
| 1. Synthetic observations | Fixed seed and minimal config | Observation table/time series | Shape, dates, geographies, signal names, metadata |
| 2. HMM/posterior or mocked posterior | Observations or deterministic fixture | Posterior stress probabilities/states | Values in `[0, 1]`, stable length, deterministic high/low cases |
| 3. BSI | Posterior/components | `BSIResult` or equivalent MVP score object | Bounded score, expected severity, required MVP fields |
| 4. Alert decision | BSI and geo/context metadata | `AlertDecision` | Alert/suppression decision matches fixture expectations |
| 5. Report output | Alert decision and context | Structured JSON and/or Markdown report | Contains score, decision, warnings, demo status, timestamp |
| 6. Dashboard JSON payload | BSI/alert/report objects | Frontend-consumable JSON | Schema contract and required metadata |
| 7. Frontend/static smoke | Dashboard JSON and static assets | Renderable static dashboard | Required DOM hooks/assets exist and consume fixture fields |

## Stage details

### Stage 1 — Synthetic observations

- **Purpose:** Provide deterministic input without live providers.
- **Preferred source:** Existing synthetic workflow if it can be made fast and deterministic.
- **Fallback source:** A small test fixture with 2 geographies, 3 signals, and 12-20 time points.
- **Required fields:** `date`, `geo`, signal columns or normalized signal values, seed/config metadata, `synthetic_only=true`.
- **Validation checks:**
  - Dates are monotonic within each geography.
  - No required signal column is missing.
  - Missingness, if present, is intentional and recorded.
  - Output is identical across two runs with the same seed after excluding generation timestamps.
- **Network access:** No.
- **External credentials:** No.

### Stage 2 — HMM/posterior or mocked posterior

- **Purpose:** Produce stress posterior inputs for BSI scoring.
- **Preferred path:** Run the adaptive HMM over synthetic observations.
- **Fallback path:** Use a mocked posterior fixture when the HMM path is too slow or when testing downstream modules independently.
- **Required fields:** `date`, `geo`, `stress_posterior`, optional `state`, optional model/version metadata.
- **Validation checks:**
  - Posterior values are numeric and bounded in `[0, 1]`.
  - At least one fixture row produces a low/no-alert score.
  - At least one fixture row produces an elevated/alert candidate score.
  - Model or fixture provenance is explicit.
- **Network access:** No.
- **External credentials:** No.

### Stage 3 — BSI computation

- **Purpose:** Convert posterior/component inputs into the implemented MVP Behavioral Stress Index representation.
- **Input contract:** Deterministic posterior plus any required precomputed components expected by `BehavioralStressIndex`.
- **Required output:** Bounded BSI score, severity/band label as implemented, component contributions if available, warnings/quality notes if available, and explicit `experimental`/`synthetic_only` metadata.
- **Validation checks:**
  - Score is within the documented range.
  - Severity/band is deterministic for known fixture values.
  - Penalty behavior is covered by at least one low-quality or drift fixture if supported by the current implementation.
  - Missing baselines/components fail with a clear error or produce an explicit confidence downgrade, depending on intended implementation.
- **Network access:** No.
- **External credentials:** No.

### Stage 4 — Alert decision

- **Purpose:** Convert BSI output into an alert decision using the existing alert engine.
- **Input contract:** BSI score/result plus geography and context metadata.
- **Required output:** Alert decision status, geo, timestamp/date, BSI, criteria, suppressions, warnings, confidence or quality metadata if available.
- **Validation checks:**
  - High fixture produces the expected alert or suppression outcome.
  - Low fixture does not alert.
  - Suppression reasons are visible when suppression occurs.
  - Cooldown behavior is deterministic within a single in-memory run.
  - Output includes enough fields for reporting and dashboard payload generation.
- **Network access:** No.
- **External credentials:** No.

### Stage 5 — Report output

- **Purpose:** Generate user-facing and machine-readable output from the alert decision.
- **Input contract:** Alert decision, BSI context, and synthetic provenance metadata.
- **Required output:** Structured JSON report and, if currently supported, Markdown report.
- **Validation checks:**
  - Report includes geo, date/timestamp, score, decision level, suppressions/warnings, and synthetic/demo status.
  - Markdown generation, if used, does not omit critical warnings present in JSON.
  - Report contains no real-world predictive claim.
  - Report is serializable and stable after excluding timestamp fields.
- **Network access:** No.
- **External credentials:** No.

### Stage 6 — Dashboard JSON payload

- **Purpose:** Produce the JSON consumed by the Chrome-friendly static/dashboard frontend.
- **Input contract:** BSI result(s), alert decision(s), report output, and lineage metadata.
- **Required output fields:**
  - `metadata`: generation time, mode, synthetic/demo flag, data source, config/model versions if available.
  - `series`: dates and BSI or posterior-derived values clearly labeled.
  - `geographies`: rows or summaries required by the frontend.
  - `alerts`: alert decisions mapped into frontend-consumable form without losing suppressions/warnings.
  - `report`: structured report payload or sanitized Markdown text.
- **Validation checks:**
  - JSON validates against a lightweight schema or golden fixture.
  - Required frontend fields are present and non-null.
  - Demo/synthetic labeling is present.
  - No field silently drops alert suppressions or warnings.
- **Network access:** No.
- **External credentials:** No.

### Stage 7 — Frontend/static smoke test

- **Purpose:** Ensure static assets can consume the dashboard JSON fixture.
- **Input contract:** Generated dashboard JSON plus `frontend/` static files.
- **Required smoke checks:**
  - `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css` exist.
  - DOM hooks referenced by JavaScript exist in HTML.
  - The fixture contains every field the JavaScript expects.
  - Demo/synthetic status is displayed or testably available to display.
  - Optional browser test loads the page in Chromium/Chrome and verifies core sections render.
- **Network access:** No for static checks; no after browser dependencies are installed for browser smoke.
- **External credentials:** No.

## Recommended test layering

### Layer 1 — Fast unit contracts

- BSI deterministic fixture tests.
- Alert decision fixture tests.
- Report serialization tests.
- Dashboard JSON schema tests.

**Expected runtime:** seconds.

### Layer 2 — Offline integration path

One test or script validates:

```text
synthetic fixture or generated observations
-> mocked posterior or HMM posterior
-> BSI
-> alert decision
-> report
-> dashboard JSON
-> static frontend contract
```

**Expected runtime:** under one minute for CI if mocked posterior is used; acceptable to run slower HMM path separately.

### Layer 3 — Optional environment-dependent checks

- Docker build/run smoke.
- Browser e2e smoke.
- Live Google Trends integration.

These must be opt-in and skipped by default when dependencies, browser tooling, or network access are unavailable.

## Proposed commands once implemented

These commands are targets for future implementation and should not be assumed to pass until the fixes are complete:

```bash
pytest tests/test_google_trends_ingestion.py
pytest tests/test_bsi_contract.py tests/test_geo_alerting.py
pytest tests/test_end_to_end_pipeline.py tests/test_frontend_static.py
pytest
```

Optional environment-dependent targets:

```bash
RUN_LIVE_TRENDS_TESTS=1 pytest -m live_trends
pytest -m browser
docker build -f docker/Dockerfile .
```

## Acceptance criteria for the first end-to-end milestone

1. Default offline `pytest` passes.
2. A deterministic fixture can produce one no-alert case and one elevated or suppressed-alert case.
3. BSI, alert, report, and dashboard payload schemas are tested together.
4. Dashboard JSON contains explicit synthetic/demo metadata.
5. Frontend static tests verify that required payload fields and DOM hooks are aligned.
6. Generated reports and dashboard payloads preserve warnings, suppressions, and provenance.
7. No validation path requires network access or credentials unless explicitly marked opt-in.

## Out-of-scope for the first end-to-end milestone

- Prospective real-world validation.
- Live Google Trends reliability guarantees.
- Production authentication, TLS, service-level objectives, rollback automation, or managed persistence.
- New UI features beyond honest labeling, schema compatibility, and smoke-tested rendering.
- Replacing the current workflow, alerting, or dashboard architecture.
