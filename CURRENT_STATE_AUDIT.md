# Current State Audit

Audit date: 2026-05-07  
Branch audited: current working branch `work` against the local checkout of `Spbd1/Early-Behavioral-Stress-Detection`  
Scope: strict repository-state audit only. No source code was modified for this audit.

Update 2026-05-07: Documentation and BSI consistency fixes have been applied for the synthetic-demo/BSI scope only. The README now states that the validated runnable demo remains synthetic and that real Google Trends ingestion is experimental. The BSI implementation is explicitly labeled as an MVP BSI and now serializes safety fields including reliability, warnings, limitations, and the not-recession-prediction warning. Alert persistence, Google Trends ingestion behavior, and frontend behavior remain unchanged.

Update 2026-05-07 (alert persistence and offline smoke validation): A small JSONL-backed alert history store now exists alongside the default in-memory store. Alert histories can be loaded/replayed from serialized decision records, and the offline smoke test exercises synthetic/mocked observations through MVP BSI computation, geo-aware alert decisions, conservative report generation, and dashboard-ready JSON payload serialization without live Google Trends, API keys, or network access. Report language guardrails now assert the safe phrase “behavioral stress signal increased” and reject the unsafe phrase “recession is coming.” Low-confidence city/metro and unsupported geography cases are covered by tests that warn or suppress instead of emitting misleading high-confidence alerts. Google Trends ingestion now has offline mock/dry-run reliability fixes; frontend architecture remains unchanged.


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

## Executive summary

This repository remains an **experimental research prototype**, not a production system. The most mature path is the synthetic-data workflow around the adaptive HMM, synthetic validation artifacts, static/browser dashboard payload generation, and basic operational metadata. Several recently added capabilities are present as useful MVP modules, but they are not integrated into a tested end-to-end live pipeline.

Historical audit note: Google Trends ingestion tests previously failed due to YAML/config parsing and validation-threshold issues. In the final local validation run on 2026-05-07, `pytest` passed offline with 50 tests, including Google Trends ingestion tests. Live/provider ingestion remains unvalidated.

The second major issue is that `BSI_DESIGN.md` is explicitly design-only and describes a richer, local-baseline, robust-anomaly, cross-signal-agreement, confidence, calibration, and uncertainty framework than the implemented `BehavioralStressIndex`. The implementation is now labeled as an MVP scalar combiner over precomputed inputs; it documents deferred design components and serializes score, severity band, uncertainty band, reliability proxy, top contributors, limitations, experimental warnings, and a not-recession-prediction warning. It still does not implement most of the design document's upstream feature construction or calibrated uncertainty.

The third major issue is that the Chrome-friendly dashboard/API path is primarily a synthetic-artifact viewer. It derives an approximate BSI-like line directly from the final posterior state, creates hard-coded synthetic geographies, and does not consume the new alert engine or report generator. This is acceptable as a demo, but it is inconsistent with the richer alert/report modules and must not be presented as a validated BSI dashboard.

## Component classification

| Component | Classification | Strict assessment |
|---|---|---|
| README scientific framing | MVP IMPLEMENTED | Cautious disclaimers are strong and accurate for research use. README now separates the validated synthetic demo from experimental real Google Trends ingestion and avoids production/prediction claims. |
| Synthetic data workflow | MVP IMPLEMENTED | Runs through synthetic generation, preprocessing, HMM, metrics, output artifacts, and lineage metadata. Validation remains synthetic-only. |
| Adaptive HMM implementation | MVP IMPLEMENTED | Covered by tests and used by synthetic workflow. No prospective real-data validation. |
| Ontology-guided keyword generation | MVP IMPLEMENTED | Deterministic ontology, local RAG retrieval, candidates, validation, review states, and registry persistence exist. No LLM integration or live keyword performance validation. |
| Local RAG grounding | MVP IMPLEMENTED | Local JSONL lexical retriever exists and is appropriately scoped to explanation/grounding only. It is not semantic RAG and has no citation-quality validation. |
| Geo-aware keyword support | PARTIAL | Keyword geo metadata and registry support stable codes, support flags, low-volume flags, and locale. Provider-code validation and provider support checks are manual. |
| Google Trends ingestion | EXPERIMENTAL / OFFLINE-MOCK VALIDATED | Pipeline exists, but config parsing tests fail, sample YAML uses block lists unsupported by the local YAML shim, and live pytrends behavior is unvalidated. Documentation now labels real ingestion as experimental and outside the validated synthetic demo path. |
| Optional pytrends dependency handling | PARTIAL | `pytrends` is optional extra, but missing dependency raises at pipeline/client construction without a tailored diagnostic or preflight check. |
| BSI design document | COMPLETE as design-only | The document is clear that it is design-only and provides rich requirements. It should not be read as implemented. |
| BSI implementation | MVP IMPLEMENTED / PARTIAL DESIGN COVERAGE | A bounded weighted composite exists and is explicitly labeled MVP BSI. The serialized output includes score, severity band, uncertainty band, reliability proxy, top contributors, limitations, experimental warnings, not-recession-prediction warning, implementation label, and components. It still omits most design-spec feature generation, calibration, volume-aware reliability, and robust uncertainty. |
| Geo normalization/local baselines | PARTIAL | Simple per-geo mean/std z-score store exists. It is not rolling, robust, seasonal, leakage-safe, persistent, or integrated into BSI computation. |
| Geo-aware alert engine | MVP IMPLEMENTED | Conservative engine with suppressions, cooldown, warnings, confidence, in-memory history, and optional JSONL persistence exists. It is still not calibrated on real data. |
| Alert false-positive suppression | PARTIAL | Heuristic suppressions exist for low breadth, anomaly, persistence, drift, data quality, geo reliability, unsupported geos, and cooldown. No news/holiday/viral-topic/seasonality suppression. |
| Persistent alert history | MVP IMPLEMENTED | Default `AlertHistory` remains in-memory for unit tests; optional `JsonlAlertHistory` persists decision records and reloads/replays JSONL history. |
| Report generation | MVP IMPLEMENTED | Structured JSON and Markdown report generator exists over alert decisions. It is not wired to a CLI/API endpoint in the browser dashboard path and has limited narrative depth. |
| Chrome-friendly browser dashboard | PLACEHOLDER | Static frontend is usable as a browser demo, but backed by synthetic payloads and hard-coded locations. It does not use implemented BSI/alert/report modules. |
| Dashboard/API consistency | PARTIAL | API serves the same static-style payload the frontend expects. It is inconsistent with alerting/reporting module schemas. |
| Streamlit dashboard | MVP IMPLEMENTED | Existing synthetic dashboard path is documented; no evidence it uses new BSI/geo-alert/report stack. |
| Docker config | PARTIAL | Dockerfile and compose exist for demos. They are not production hardened and may fail if tests/config parsing failures affect build or runtime. |
| Experimental production hardening | PARTIAL | Config validation, healthcheck, environment checks, lineage, model version metadata, structured logging, and docs exist. There is no real deployment controller, auth, TLS, SLA, rollback automation, or secret store integration. |
| CI | BROKEN | Workflows exist and run tests/builds, but local `python -m pytest` currently fails. |
| Test coverage | PARTIAL | There are tests for synthetic workflow, HMM, ops, frontend static shape, keyword generation, geo alerting, ingestion, persistent alert history, report language safety, geo suppressions, and an offline BSI-alert-report-dashboard smoke path. Missing: live provider integration, full dashboard/API schema contract with frontend architecture, BSI design conformance, Docker runtime smoke, browser e2e. |
| Reproducibility | MVP IMPLEMENTED | Synthetic deterministic seed, output artifacts, lineage hashes, git commit, and model version ID exist. Live ingestion reproducibility remains weak due to provider sampling and config parser issues. |
| Data lineage | PARTIAL | Synthetic workflow has artifact lineage. Google Trends ingestion metadata exists but lacks artifact hashes/model-version integration and live provenance validation. |
| Model/version metadata | PARTIAL | Synthetic workflow computes a model version from lineage. BSI/alert/report/dashboard payloads do not consistently include model, config, data, keyword registry, or provider versions. |
| Security and secret handling | PARTIAL | No secrets are committed; environment validator redacts secret-like vars. API has no authentication, authorization, TLS, CORS policy, request limits, audit log, or production secret integration. |

## What is actually implemented

### Synthetic research pipeline

- A reproducible synthetic workflow exists: configuration load/validation, synthetic aggregate data generation, codebook validation, winsorization/standardization, Adaptive HMM fit/predict, posterior/filtered/Viterbi/transition outputs, metrics, lineage, and run metadata.
- The workflow writes expected CSV and JSON artifacts under the configured output directory.
- Deterministic random seed handling and artifact hashing are implemented for synthetic workflow outputs.
- This is the most coherent end-to-end path in the repository.

### Adaptive HMM and validation scaffolding

- Adaptive HMM code and synthetic validation metrics are implemented and covered by tests.
- The model path remains a research approximation. It is not calibrated to recession outcomes and has no prospective real-world validation.

### Ontology-guided keyword generation

- A controlled keyword ontology exists with stable categories and expected stress directions.
- A deterministic keyword generation pipeline combines seed terms, geo metadata, ontology category guidance, and local retrieval context.
- A geo-aware keyword registry supports candidate addition, deduplication, semantic grouping, reviewer transitions, retirement, drift-review status, history, unsupported-location tracking, and JSON persistence.
- A validation pipeline checks category membership, RAG grounding, confidence score, geo support, low-volume flags, locale, and whether a generated candidate incorrectly enters as already approved.
- This is an MVP governance workflow, not an autonomous keyword discovery system.

### Local RAG grounding

- A local JSONL knowledge base and lexical retriever are implemented.
- Retrieval is deterministic and uses token overlap plus small geography/locale bonuses.
- The implementation correctly keeps RAG away from alert decisions.
- It is not embedding-based semantic retrieval, not an LLM grounded generation system, and not a substitute for reviewer evidence quality checks.

### Google Trends ingestion layer

- Classes exist for typed-ish ingestion config, file cache, pytrends-backed client, retry/backoff, rate limiting, batching, raw batch writes, processed long-format panel generation, anchor normalization, incremental timeframe selection, validation flags, JSON logging, CLI, and script entry point.
- A small `TrendsClient` protocol enables test fixtures.
- Raw and processed storage separation is implemented.

However, the current implementation is broken enough that it should not be described as reliable live ingestion.

### BSI implementation

- `BehavioralStressIndex.compute()` accepts already-computed component scores and returns score, severity band, uncertainty band, top contributing signals, recent change, explanation, limitations, and components.
- It clamps components, applies fixed weights, subtracts drift and quality/geography penalties, and maps score to bands `watch/yellow/orange/red`.
- This is an MVP scoring utility over prepared inputs, not the full BSI design.

### Geo-aware alert engine

- Alert observation, policy, decision, in-memory history, and evaluation logic are implemented.
- Suppression rules cover insufficient keyword-family agreement, low anomaly confirmation, low persistence, low drift confidence, low data quality, low geographic reliability, unsupported geography, low quality floor, warnings for low-scoring cases, and cooldown.
- Explanations and ontology movers are included.
- History is in memory only.

### Report generation

- A report generator produces structured JSON-like dicts and Markdown from alert decisions and optional geo comparison payloads.
- It includes summary, where/what changed, contributing signals, ontology movers, broad/localized text, uncertainty, confounders, limitations, counts, and guardrails.

### Browser dashboard/API

- A stdlib `ThreadingHTTPServer` serves frontend static files and `/api/health` plus `/api/dashboard.json`.
- Dashboard payload builder reads synthetic `posterior.csv`, `observations.csv`, `metrics.csv`, and `viterbi_path.csv`.
- Static frontend has selectors, canvas charts, alert timeline, signal table, quality/drift warning lists, geo table, and JSON report export.
- This is a Chrome-friendly synthetic demo, not a live alerting dashboard.

### Experimental operations hardening

- Health reports combine config and environment checks.
- Runtime config validation checks synthetic/model/basic deployment settings.
- Environment validation checks required vars/paths and redacts secret-like variable state.
- Lineage manifests hash artifacts and record git commit/Python version.
- CI workflows exist for Python 3.10/3.11 tests, compile checks, synthetic smoke, frontend payload build, and Docker build.
- Dockerfile and compose services exist for research demo, dashboard, Streamlit, and Langflow.

## What is only documented

- Full BSI design: robust local rolling baselines, median/MAD anomalies, seasonality/holiday/event adjustment, calibrated monotone transforms, empirical CDF scaling, formal confidence score, reliability labels, uncertainty propagation/bootstrap, required output schema, anti-spike protections, and calibrated severity thresholds.
- Production-hardening goals such as rollback procedures, production deployment, incident response, and secret management are mostly documentation and configuration guardrails, not an implemented production control plane.
- Google Trends limitations and reliability cautions are documented more thoroughly than they are enforced in code.
- Provider geography limitations and future LLM metadata requirements for keyword generation are documented but not operationalized.
- Chrome/dashboard claims around broad BSI/geographic comparison are only demo-level in code.

## What is placeholder or demo-only

- Browser dashboard geo comparison is hard-coded synthetic geography data derived from the latest posterior-derived BSI-like value.
- Dashboard BSI series is not produced by `BehavioralStressIndex`; it is `posterior[last_state] * 100`.
- Dashboard alerts are simple threshold crossings on that synthetic series, not `GeoAwareAlertEngine` decisions.
- Dashboard report is a small synthetic summary, not `ReportGenerator` output.
- Local RAG seed knowledge base is suitable for deterministic tests/examples, not evidence-grade retrieval.
- Langflow assets and custom components appear to be scaffold/demo integrations rather than a validated orchestrated production workflow.
- Production config uses `data.source: synthetic`; it is an experimental profile, not live production config.
- Several local shim packages under `src/` (`yaml`, `scipy`, `sklearn`, `statsmodels`, `plotly`, `streamlit`) are compatibility/test scaffolds and create risk of shadowing real packages.

## What is broken or inconsistent

### Test suite is currently failing

`python -m pytest` collected 34 tests and failed 2 Google Trends ingestion tests:

1. `test_validation_flags_sparse_and_unstable_anchor` expected a `low_nonzero:rare` validation issue, but the configured default threshold and strict `<` comparison do not flag exactly `0.25` nonzero fraction.
2. `test_load_ingestion_config_supports_nested_sections` expected YAML inline list parsing for `keywords: [anchor, kw]`, but the local `src/yaml.py` parser returns the string `"[anchor, kw]"`.

Because CI runs `pytest`, this is a release-blocking inconsistency.

### YAML/config parsing status

- The repository shadows PyYAML with `src/yaml.py`.
- The shim parser now supports simple nested mappings plus block and inline scalar lists used by the ingestion sample config.
- It remains a small compatibility shim rather than a complete YAML implementation.

### Google Trends ingestion reliability status

- Live pytrends use is not validated in tests and remains experimental.
- `pytrends` is optional for package imports, tests, and dry-run ingestion; live `PytrendsClient` construction now raises a clear install/dry-run error when pytrends is unavailable.
- Dry-run ingestion uses a deterministic mock client and validates raw CSV, processed panel CSV, and metadata JSON artifacts before returning paths.
- There is retry/backoff, rate limiting, cache, validation, and artifact schema checking, but no robust live-provider guarantee for Google throttling semantics, provider rescaling across runs, or canonical provider errors.
- Anchor quality gates are recorded and artifact schemas are enforced; live analytical use still requires review of quality warnings before downstream analysis.
- Incremental ingestion scans processed files by region and creates an overlapping date request, but immutable point-in-time snapshot manifests remain pending.

### BSI design/implementation mismatch

- Design says status is design-only, but README and module names may lead readers to infer BSI is implemented end-to-end.
- Design recommends components H, A, B, P, C, T with MVP weights 0.25/0.25/0.15/0.15/0.15/0.05; implementation uses HMM 0.24, anomaly 0.18, breadth 0.14, persistence 0.14, acceleration 0.10, data quality 0.08, drift confidence 0.06, geographic confidence 0.06.
- Design treats quality/drift/confidence mostly as confidence/uncertainty adjustments; implementation subtracts fixed drift and quality penalties directly from the score.
- Design requires geography/date/confidence/reliability/90% uncertainty/experimental flags/not-recession-prediction/data quality notes; implementation output omits several of these fields.
- Design recommends robust rolling local baselines, seasonality adjustment, anti-spike protections, and calibration; implementation assumes all components are already prepared.
- Design uses severity bands normal/elevated/mild/significant/extreme over 0-20/20-40/40-60/60-80/80-100; implementation uses watch/yellow/orange/red with thresholds 45/60/75.

### Geo normalization gaps

- `GeoBaselineStore` computes global mean/std per geography over the provided history, not rolling, seasonal, robust median/MAD, or leakage-safe baselines.
- Baselines are in memory only and not versioned/persisted.
- Missing baselines raise immediately; there is no fallback strategy, roll-up behavior, or confidence downgrade.
- Google Trends provider geo codes are stored in keyword metadata but not validated against pytrends/Google support.

### Alert engine consistency gaps

- Alert history is process-local memory only and disappears on restart.
- Cooldown logic uses the same in-memory history and cannot suppress duplicates across deployments or API restarts.
- Suppression is heuristic and uncalibrated. It does not include news shock detection, holiday/seasonality adjustment, viral topic suppression, or known local event confounders.
- Alert decisions are not produced by the dashboard payload builder.

### Dashboard/API inconsistencies

- API `/api/dashboard.json` emits synthetic static-dashboard schema, not `AlertDecision` or `StressReport` schema.
- Frontend expects `alerts` with `date`, `level`, `message`, while alert engine decisions use `timestamp`, `geo`, `bsi`, `criteria`, suppressions, warnings, etc.
- Frontend geo table expects `country`, `region`, `city`, `bsi`; geo comparison builder emits nested geo rows and normalized signal series.
- Frontend report displays a demo report dict, not Markdown or structured output from `ReportGenerator`.
- Selectors do not filter chart data by selected geography; they mostly alter dropdown state and rerender the same synthetic payload.

### Docker/production config inconsistencies

- Dockerfile installs `-e .` only, not optional extras for pytrends/langflow except the compose `langflow` service installing langflow at runtime.
- The runtime command is synthetic demo by default; compose dashboard runs synthetic demo, static payload build, and dashboard server.
- No auth token is enforced by the API server even though production experimental config lists `BEHAVIORAL_STRESS_API_TOKEN` as a secret env var.
- Healthcheck returns success for `ok` or `degraded`, which is acceptable for a demo but weak for production gating.

## What cannot be validated without external credentials or network access

- Live Google Trends retrieval through pytrends, including throttling, rate limits, provider changes, regional availability, and sampled/rescaled data stability.
- Whether configured Google Trends `geo` codes and city/metro mappings are supported by Google for the selected keywords/timeframes.
- Whether live ingestion outputs are stable across repeated pulls and cache TTL windows.
- Whether optional dependencies install cleanly in a fresh networked environment for all extras (`pytrends`, `langflow`, advanced packages).
- Docker build behavior against current package indexes and platform-specific dependency resolution.
- Any claim about real-world predictive value, prospective early-warning performance, or calibration against macroeconomic outcomes.
- Browser behavior beyond static-file smoke checks unless a real browser/e2e environment is used.
- Security behavior behind real reverse proxies, TLS termination, auth gateways, or secret stores.

## What needs tests

Priority tests to add or repair:

1. Fix Google Trends ingestion unit tests and YAML parser/config loading tests.
2. Add tests that sample Google Trends YAML config loads into real lists and correct typed fields.
3. Add missing-`pytrends` preflight/diagnostic tests.
4. Add live-provider integration tests behind an explicit opt-in marker, never required for offline CI.
5. Add BSI design-conformance tests for output fields, bands, penalty behavior, and edge cases.
6. Add tests comparing `BSI_DESIGN.md` required output fields against `BSIResult` or explicitly documenting the reduced MVP schema.
7. Add geo baseline tests for leakage avoidance, rolling-window behavior, sparse geographies, low-volume roll-up, and persistence/versioning once implemented.
8. Add persistent alert history tests once a durable backend exists.
9. Add alert false-positive suppression tests for isolated single-signal spikes, missing data, low geo reliability, cooldown across restart, and confounder flags.
10. Add dashboard/API contract tests that validate frontend expected schema against `/api/dashboard.json`.
11. Add tests ensuring dashboard payload can consume real alert/report outputs or explicitly remains synthetic-demo-only.
12. Add browser e2e smoke in Chromium/Chrome for loading, chart rendering, selector behavior, and export button.
13. Add Docker build/run smoke tests for synthetic demo and dashboard service.
14. Add security tests for secret redaction, absence of committed credentials, and API auth behavior if introduced.
15. Add lineage tests for ingestion artifacts, keyword registry versions, BSI configuration versions, and dashboard payload metadata.
16. Add reproducibility tests for deterministic synthetic output hashes on supported Python versions.

## Unsafe for real production

The current repository is unsafe for real production because:

- End-to-end live pipeline is not tested.
- Google Trends ingestion is currently broken at the config/test layer and unvalidated live.
- There is no durable alert history or replayable alert state.
- There is no production authentication/authorization on the dashboard API.
- There is no TLS, rate limiting, CORS policy, audit logging, or request hardening in the stdlib server.
- The dashboard can imply geographic comparison despite synthetic/hard-coded geography rows.
- BSI output is not calibrated, prospectively validated, or aligned with the full design specification.
- Alert thresholds and suppressions are heuristic and uncalibrated.
- No real data lineage connects provider request, keyword registry version, BSI component transforms, model version, alert decision, report, and dashboard payload.
- No incident response, rollback controller, deployment promotion gate, or model-risk governance is implemented.
- Optional dependency installation and provider behavior are not guaranteed.
- Local shim modules can shadow real scientific packages and create environment-specific behavior.
- No privacy/legal/provider-terms review is encoded for live provider ingestion.

## Acceptable for experimental research use

The repository is acceptable for cautious experimental research use if users keep the following boundaries:

- Use the synthetic workflow to study latent regime detection mechanics and reproducibility.
- Use keyword generation/registry/RAG modules as a governed candidate-review scaffold, not as an autonomous signal generator.
- Use Google Trends ingestion only after fixing config parsing/tests and treating live outputs as sampled, unstable, provider-normalized research data.
- Use BSI and alerting modules as prototype interfaces over controlled/precomputed inputs, not as validated public alerts.
- Use dashboard/API as a synthetic browser demo, not as an operational monitoring console.
- Preserve all existing caveats: no recession prediction, no policy automation, no individual-level inference, and no causal claims.

## README accuracy review

Accurate or appropriately cautious:

- The README's main framing says the project is experimental, synthetic-first, not a validated recession predictor, not a production forecasting system, and not for individual diagnosis or policy prescription.
- The synthetic demo and validation caveats are directionally accurate.
- Ontology/RAG documentation correctly states RAG is for explanation/grounding and cannot bypass reviewer approval.
- Google Trends tradeoffs and limitations are documented with appropriate caution.

Needs correction or clarification:

- Optional extras list omits `pip install -e .[ingestion]` in the initial optional extras block even though the ingestion section later mentions it.
- The README says ingestion config loads typed YAML settings, but current YAML parsing is broken for inline and block lists in tests/sample config.
- The README's dashboard description mixes the older Streamlit synthetic dashboard with newer Chrome-friendly dashboard concepts; the Chrome dashboard is synthetic/demo-only and should be labeled as such wherever mentioned.
- Addressed for current docs: the README says `BSI_DESIGN.md` is design-only and the implemented BSI is an MVP utility that does not implement the full design.
- Addressed for README-level claims: wording that implied Google Trends ingestion is ready for live collection has been softened; config parsing, optional dependency handling, and live-provider validation still need fixes.

## Data lineage and metadata review

Implemented:

- Synthetic workflow records artifact hashes, git commit, Python version, deterministic metadata, config path, model config, model version, config validation report, output paths, and warning label.
- Ingestion metadata records run ID, started/finished timestamps, config, per-region timeframes, raw paths, and validation results.

Gaps:

- Ingestion artifacts are not hashed in a lineage manifest.
- Keyword registry version/history is not linked to ingestion runs, BSI runs, alerts, reports, or dashboard payloads.
- BSI scoring does not include input transform version, weight version, calibration version, or design-version metadata.
- Alert decisions do not include model version, data snapshot hash, keyword registry version, provider request hash, or code version.
- Dashboard payload does not expose lineage/model/version metadata prominently.

## Security and secret-handling review

Acceptable for research/demo:

- No obvious secrets were found in config examples inspected during audit.
- Environment validation reports secret-like variable state without printing values.
- CI permissions are read-only for repository contents.

Unsafe for production:

- API server has no authentication despite token config existing.
- No TLS or reverse-proxy hardening is part of the app.
- No authorization model, user audit log, request logging policy, or rate limiting.
- No structured secret-store integration or rotation policy in code.
- Static server path translation is minimal and should not be exposed as a hardened production server.

## Bottom line

Strict classification of the whole project: **experimental MVP / research prototype for synthetic and offline/mock paths; partial and unvalidated for live Google Trends + calibrated BSI + geo-alert production pipeline; not production-ready.**

Before any production claim, the project needs a green test suite, fixed YAML/config loading, explicit pytrends preflight handling, live ingestion validation, BSI design/implementation reconciliation, persistent alert history, dashboard/API schema alignment, durable lineage across all outputs, calibrated thresholds, security controls, and full end-to-end tests.

## Google Trends ingestion reliability/offline-testability update

Completed on 2026-05-07:

- pytrends remains an optional dependency: importing the ingestion package and running offline tests no longer requires pytrends, while live `PytrendsClient` construction raises an explicit install/dry-run error if pytrends is missing.
- Added deterministic Google Trends dry-run/mock ingestion that writes raw provider-shaped CSVs, processed long-format panels, and run metadata without network access or secrets.
- Added artifact validators for raw provider response CSVs, processed long-format panel CSVs, and run metadata JSON, including required columns/fields, date parsing, numeric checks, duplicate checks, and artifact path checks.
- Run metadata now preserves geography metadata for country/region/city-style inputs, records unsupported or low-volume geography warnings, and repeats the limitation that raw Google Trends values are scaled within each request and must not be naively compared across regions.

Still deferred: live Google Trends reliability claims, provider terms/legal review, scheduled live operation, and calibrated use of real-world Google Trends signals.

## Dashboard/API/static frontend consistency update

Completed on 2026-05-07 for the dashboard/API/frontend scope only:

- The browser dashboard payload now has an explicit `dashboard.v1` schema version, experimental system metadata, a not-recession-prediction claim guardrail, canonical warning groups, geo metadata, report export metadata, and static-mode metadata stating that no backend is required when `frontend/dashboard.json` is generated.
- Backend payload aliases used by the frontend (`quality_warnings`, `drift_warnings`, `geo_reliability_warnings`, `report`, and `locations`) are kept in sync with canonical fields so the API-backed and generated-static paths render the same fields.
- A dependency-free schema validator and pytest snapshot-style contract check now cover BSI rows, alerts, geo comparison rows, warning groups, reports, and static-mode behavior.
- The frontend now displays data-quality, drift, and geo reliability warnings, labels the page as experimental, repeats the not-recession-prediction guardrail from the payload, and exports a JSON report in static or API-backed mode.
- The static frontend remains framework-free and uses broadly supported Chrome APIs (`fetch`, canvas, `Blob`, and `URL.createObjectURL`) while avoiding known experimental browser APIs in the smoke test.

Still not claimed:

- The browser dashboard remains synthetic/demo-oriented and does not validate real-world monitoring, calibrated BSI thresholds, or recession prediction.
- The geo comparison display is a reliability-aware synthetic table/placeholder, not a validated map product.
- A static file server such as `python -m http.server --directory frontend` is still recommended for Chrome static mode; opening `index.html` directly from `file://` may be blocked by browser fetch restrictions.
