# Prioritized Fix Plan

Source audit: `CURRENT_STATE_AUDIT.md` dated 2026-05-07. This plan is intentionally limited to planning and validation design except where status notes record completed narrow fixes.

Update 2026-05-07: The documentation and BSI consistency slice of A2/C1/C2/E2 has been implemented. README now labels the validated runnable demo as synthetic and real Google Trends ingestion as experimental. BSI is labeled MVP, documents implemented/deferred design components, and serializes reliability, warnings, limitations, top contributors, an experimental warning, and a not-recession-prediction warning. Alert persistence, Google Trends ingestion behavior, and frontend behavior were intentionally not changed.

## Prioritization principles

1. Restore correctness first: make required offline tests deterministic and green before adding functionality.
2. Prefer observability and reproducibility: every pipeline artifact should carry enough metadata to explain how it was produced.
3. Keep demo, MVP, and design-only claims separate: do not present synthetic/dashboard demos as validated production behavior.
4. Add end-to-end seams before expanding scope: wire existing modules through a minimal offline path before introducing live providers.
5. Require explicit opt-in for networked or credentialed validation: offline CI must remain reliable.

## Priority legend

- **P0:** Blocks trust in current repository state or offline CI.
- **P1:** Blocks a minimal end-to-end research demo with coherent artifacts.
- **P2:** Important hardening or validation before any pilot use.
- **P3:** Longer-term research/product maturity work.

## A. Critical correctness fixes

### A1. P0 — Restore Google Trends ingestion config correctness

- **Problem:** Google Trends ingestion tests currently fail due to YAML/config parsing and threshold expectation mismatches.
- **Why it matters:** The repository cannot be considered green while default `pytest` fails, and ingestion documentation cannot be trusted if sample config cannot load correctly.
- **Files likely affected:** `src/yaml.py`, `src/behavioral_stress/ingestion/config.py`, `src/behavioral_stress/ingestion/trends.py`, `configs/ingestion/google_trends_sample.yaml`, `tests/test_google_trends_ingestion.py`.
- **Risk level:** High. Config parsing changes can affect every command that loads YAML.
- **Implementation approach:** Add narrowly scoped support for the YAML structures used by repository configs, or replace the local shim path with a reliable parser already declared as a dependency. Normalize loaded config fields into typed lists and numbers before validation. Align threshold validation tests with intended semantics rather than implementation accidents.
- **Validation method:** Run the targeted Google Trends ingestion tests, then full offline `pytest`.
- **Expected result:** Sample ingestion YAML loads into typed structures, threshold validation is deterministic, and offline tests pass without network access.
- **Requires network access:** No.
- **Requires external credentials:** No.

### A2. P0 — Clarify BSI implementation contract versus design document

**Status update 2026-05-07:** Documentation and MVP output-schema clarification completed for the current implementation. Remaining work is design-conformance expansion only; scoring formula calibration and upstream feature construction are intentionally deferred.

- **Problem:** `BSI_DESIGN.md` describes a richer design than the implemented `BehavioralStressIndex`, including local baselines, calibrated uncertainty, confidence, reliability, and output fields that are not implemented.
- **Why it matters:** Users can misinterpret the current BSI as design-complete, creating scientific and operational risk.
- **Files likely affected:** `BSI_DESIGN.md`, `README.md`, `src/behavioral_stress/alerting/bsi.py`, `tests/test_geo_alerting.py`, possible new BSI contract tests.
- **Risk level:** High. It changes public interpretation of core output without necessarily changing algorithms.
- **Implementation approach:** First document the implemented MVP contract explicitly. Then either rename/label missing design fields as future work or add a separate design-conformance backlog. Avoid changing the scoring formula until tests pin the current intended MVP behavior.
- **Validation method:** Add tests that assert the MVP output schema and docs claim consistency; review README and design docs for explicit design-only language.
- **Expected result:** Documentation and tests make clear which BSI fields and guarantees exist today. Current MVP fields are score, severity band, uncertainty band, reliability proxy, top contributors, limitations, warnings, implementation label, and components.
- **Requires network access:** No.
- **Requires external credentials:** No.

### A3. P0 — Prevent dashboard BSI-like synthetic line from being presented as validated BSI

- **Problem:** Dashboard payload generation derives an approximate BSI-like line from synthetic posterior state rather than consuming the implemented BSI, alert engine, or report generator.
- **Why it matters:** The dashboard can visually imply validated stress scoring even though it is currently a synthetic demo artifact.
- **Files likely affected:** `src/behavioral_stress/api/dashboard_data.py`, `scripts/build_frontend_data.py`, `frontend/app.js`, `frontend/index.html`, `README.md`, `tests/test_frontend_static.py`.
- **Risk level:** High. This is a correctness and communication issue more than a feature issue.
- **Implementation approach:** Add explicit demo metadata and labels in payload and UI. In the next wiring step, create a minimal path that can optionally consume real `BSIResult`, `AlertDecision`, and report objects while preserving the synthetic demo mode.
- **Validation method:** Contract tests assert demo metadata is present and frontend smoke tests confirm the UI labels synthetic/demo data clearly.
- **Expected result:** Dashboard output is not mistaken for validated production BSI, and future integration has a clear schema target.
- **Requires network access:** No.
- **Requires external credentials:** No.

### A4. P1 — Add deterministic minimal BSI-to-alert correctness fixture

- **Problem:** There is no single fixture proving that known posterior inputs produce expected BSI bands and alert decisions.
- **Why it matters:** Without deterministic fixtures, downstream report/dashboard behavior can drift silently.
- **Files likely affected:** `src/behavioral_stress/alerting/bsi.py`, `src/behavioral_stress/alerting/engine.py`, `tests/test_geo_alerting.py`, new fixture files under `tests/fixtures/` if needed.
- **Risk level:** Medium.
- **Implementation approach:** Define small synthetic posterior/component inputs with known expected score, severity, suppression, and alert outcome. Keep the fixture offline and independent of live providers.
- **Validation method:** Unit tests assert exact or tolerance-bounded BSI and alert outputs.
- **Expected result:** Core scoring and alert decisions are reproducible.
- **Requires network access:** No.
- **Requires external credentials:** No.

## B. Broken commands or imports

### B1. P0 — Make advertised Google Trends ingestion commands fail gracefully offline

- **Problem:** Optional `pytrends` handling is partial; construction can fail without a tailored diagnostic or preflight path.
- **Why it matters:** Users need actionable errors instead of import failures when optional live ingestion dependencies are absent.
- **Files likely affected:** `src/behavioral_stress/ingestion/trends.py`, `src/behavioral_stress/ingestion/cli.py`, `scripts/run_google_trends_ingestion.py`, `requirements.txt`, `pyproject.toml`, `tests/test_google_trends_ingestion.py`.
- **Risk level:** Medium.
- **Implementation approach:** Add an explicit dependency preflight and user-facing error message. Keep live pytrends tests behind an opt-in marker and make offline config validation runnable without pytrends.
- **Validation method:** Run tests in an environment without pytrends and assert the diagnostic text; separately run opt-in integration tests only in networked environments.
- **Expected result:** Offline users can validate configs; live ingestion clearly explains missing optional dependency.
- **Requires network access:** No for preflight; yes for live provider integration.
- **Requires external credentials:** No.

### B2. P1 — Verify documented CLI entrypoints and scripts

- **Problem:** Several scripts are documented for demos, validation, dashboard generation, and ingestion, but the audit identifies broken or unvalidated paths.
- **Why it matters:** Reproducible research requires commands in docs to run or clearly state their prerequisites.
- **Files likely affected:** `README.md`, `scripts/run_synthetic_demo.py`, `scripts/build_frontend_data.py`, `scripts/build_dashboard.py`, `scripts/run_validation.py`, `scripts/run_google_trends_ingestion.py`, `tests/test_workflow.py`, `tests/test_frontend_static.py`.
- **Risk level:** Medium.
- **Implementation approach:** Create a command inventory test or documentation checklist. Separate offline demo commands from live/provider commands and mark prerequisites.
- **Validation method:** Execute each offline command in CI with temporary output directories; check help text for live commands without network calls.
- **Expected result:** Documented offline commands run successfully and live commands provide safe dry-run/preflight behavior.
- **Requires network access:** No for offline scripts; yes only for explicit live ingestion.
- **Requires external credentials:** No for current Google Trends path, unless future providers are added.

### B3. P1 — Validate Docker demo commands against current dependency declarations

- **Problem:** Dockerfile installs the package without optional extras while compose includes runtime demo behavior and a Langflow service that installs dependencies at runtime.
- **Why it matters:** Container-based reproducibility can fail even if local tests pass.
- **Files likely affected:** `docker/Dockerfile`, `docker/docker-compose.yml`, `requirements.txt`, `pyproject.toml`, `scripts/healthcheck.py`, `docs/operations/deployment.md`.
- **Risk level:** Medium.
- **Implementation approach:** Add a documented offline Docker smoke path for synthetic demo and dashboard serving. Keep optional extras explicit and avoid silently enabling live ingestion.
- **Validation method:** Docker build plus container command smoke test in a networked CI job or local release checklist.
- **Expected result:** Demo container builds and serves synthetic dashboard consistently.
- **Requires network access:** Yes for image build dependency installation unless dependencies are cached.
- **Requires external credentials:** No.

## C. Documentation contradictions

### C1. P0 — Align README ingestion claims with failing/tested state

- **Problem:** README scientific framing is cautious overall, but ingestion/config reliability is overstated while Google Trends tests fail.
- **Why it matters:** Documentation should not claim stable ingestion while the audited branch is not green.
- **Files likely affected:** `README.md`, `docs/operations/troubleshooting.md`, `docs/reproducibility/reproducibility_guide.md`, `configs/ingestion/google_trends_sample.yaml`.
- **Risk level:** Medium.
- **Implementation approach:** Update docs after fixes to say exactly what is tested offline, what requires pytrends/network, and what remains unvalidated live.
- **Validation method:** Documentation review plus command inventory tests.
- **Expected result:** README matches tested behavior and clearly distinguishes synthetic, offline, and live paths.
- **Requires network access:** No.
- **Requires external credentials:** No.

### C2. P1 — Add explicit status labels for design-only, MVP, partial, and missing components

**Status update 2026-05-07:** BSI-related labels were added: `BSI_DESIGN.md` is design-only and `BehavioralStressIndex` is an implemented MVP BSI. Broader repository labeling remains future cleanup.

- **Problem:** The repository contains mature-looking docs for components that are implemented only partially or as design-only artifacts.
- **Why it matters:** Clear status labels reduce misuse and make roadmap sequencing more transparent.
- **Files likely affected:** `README.md`, `BSI_DESIGN.md`, `ARCHITECTURE_GAPS.md`, `ROADMAP.md`, `MILESTONE_TRACKER.md`, `docs/production_hardening.md`.
- **Risk level:** Low.
- **Implementation approach:** Reuse the audit classification terminology and add stable labels near feature descriptions. Avoid deleting aspirational design content; label it as future design.
- **Validation method:** Manual doc review and simple text checks for key warning labels.
- **Expected result:** Users can quickly tell what is implemented, partial, broken, missing, or design-only.
- **Requires network access:** No.
- **Requires external credentials:** No.

### C3. P1 — Document dashboard/API schema status and limitations

- **Problem:** API and frontend schemas are synthetic-demo oriented and inconsistent with alert/report module schemas.
- **Why it matters:** Consumers need to know whether `/api/dashboard.json` is a demo payload or a contract for alert/report outputs.
- **Files likely affected:** `README.md`, `src/behavioral_stress/api/dashboard_data.py`, `src/behavioral_stress/api/server.py`, `frontend/app.js`, `docs/operations/deployment.md`.
- **Risk level:** Medium.
- **Implementation approach:** Add a small schema status section and define a future canonical dashboard schema in tests before wiring changes.
- **Validation method:** Schema contract test for current demo payload and future integration tests for alert/report payloads.
- **Expected result:** Dashboard consumers understand current limitations and the next integration target.
- **Requires network access:** No.
- **Requires external credentials:** No.

## D. End-to-end pipeline gaps

### D1. P1 — Create one offline pipeline path from synthetic observations to report and dashboard payload

- **Problem:** Synthetic workflow, HMM, BSI, alerting, reporting, dashboard API, and frontend smoke tests exist as separate pieces, but not as one coherent validated path.
- **Why it matters:** A minimal end-to-end path is the fastest way to detect schema drift and correctness regressions.
- **Files likely affected:** `src/behavioral_stress/workflows/synthetic_workflow.py`, `src/behavioral_stress/alerting/bsi.py`, `src/behavioral_stress/alerting/engine.py`, `src/behavioral_stress/alerting/reporting.py`, `src/behavioral_stress/api/dashboard_data.py`, `scripts/build_frontend_data.py`, `tests/test_workflow.py`, `tests/test_frontend_static.py`.
- **Risk level:** High.
- **Implementation approach:** Add a thin orchestrator or test-only adapter that passes synthetic observations through HMM/posterior or a deterministic mocked posterior, computes BSI, evaluates alert decision, generates a report, builds dashboard JSON, and validates frontend assets. Do not replace existing architecture.
- **Validation method:** Implement the minimal path described in `END_TO_END_VALIDATION_PLAN.md` as an offline test.
- **Expected result:** One command validates that major modules can interoperate with stable schemas.
- **Requires network access:** No.
- **Requires external credentials:** No.

### D2. P1 — Define canonical payload adapters between BSI, alerts, reports, and dashboard JSON

- **Problem:** Current dashboard payload schema does not match `AlertDecision` or `StressReport` concepts.
- **Why it matters:** Ad hoc conversions can hide important metadata such as suppressions, warnings, confidence, and experimental status.
- **Files likely affected:** `src/behavioral_stress/api/dashboard_data.py`, `src/behavioral_stress/alerting/reporting.py`, `frontend/app.js`, `tests/test_frontend_static.py`, new schema tests.
- **Risk level:** Medium.
- **Implementation approach:** Define a small adapter layer that maps current internal objects into the dashboard payload while retaining demo metadata and warnings. Preserve backward compatibility until frontend tests cover the new fields.
- **Validation method:** Golden JSON fixture comparison and frontend static smoke test.
- **Expected result:** Dashboard payload can represent real alert/report outputs without losing critical context.
- **Requires network access:** No.
- **Requires external credentials:** No.

### D3. P2 — Add artifact lineage across ingestion, BSI, alert, report, and dashboard outputs

- **Problem:** Some lineage metadata exists, but not consistently across the full alert/report/dashboard chain.
- **Why it matters:** Reproducibility and auditability require knowing input data, model version, config version, and generation time for every output.
- **Files likely affected:** `src/behavioral_stress/ops/lineage.py`, `src/behavioral_stress/workflows/synthetic_workflow.py`, `src/behavioral_stress/alerting/bsi.py`, `src/behavioral_stress/alerting/reporting.py`, `src/behavioral_stress/api/dashboard_data.py`, `tests/test_ops_hardening.py`.
- **Risk level:** Medium.
- **Implementation approach:** Add shared metadata fields where absent; do not introduce a new storage backend yet.
- **Validation method:** Tests assert required metadata fields on generated artifacts.
- **Expected result:** Every end-to-end output can be traced to inputs and configuration.
- **Requires network access:** No.
- **Requires external credentials:** No.

## E. Test coverage gaps

### E1. P0 — Restore and gate full offline test suite

- **Problem:** Current default test suite fails.
- **Why it matters:** Further work is unsafe until regression signal is reliable.
- **Files likely affected:** `tests/test_google_trends_ingestion.py`, related ingestion/config files, CI documentation if present.
- **Risk level:** High.
- **Implementation approach:** Fix failing tests, keep live tests skipped unless explicitly enabled, and add a clear offline test command to docs.
- **Validation method:** Full `pytest` completes successfully offline.
- **Expected result:** Default local and CI testing is green.
- **Requires network access:** No.
- **Requires external credentials:** No.

### E2. P1 — Add BSI design/MVP contract tests

**Status update 2026-05-07:** Minimal BSI contract coverage added for MVP output fields and documentation status labels.

- **Problem:** There are no tests ensuring docs and implemented BSI schema remain aligned.
- **Why it matters:** BSI is central to downstream interpretation.
- **Files likely affected:** `src/behavioral_stress/alerting/bsi.py`, `BSI_DESIGN.md`, `tests/test_geo_alerting.py`, new `tests/test_bsi_contract.py`.
- **Risk level:** Medium.
- **Implementation approach:** Test required MVP fields, severity thresholds, confidence/penalty semantics as implemented, and explicit absence or future status of design-only fields.
- **Validation method:** Unit tests and doc status text checks.
- **Expected result:** BSI behavior and documentation stay synchronized.
- **Requires network access:** No.
- **Requires external credentials:** No.

### E3. P1 — Add dashboard/API contract and frontend fixture tests

- **Problem:** Frontend expectations and API payload shape can drift independently.
- **Why it matters:** Static dashboard can break even when backend unit tests pass.
- **Files likely affected:** `src/behavioral_stress/api/dashboard_data.py`, `frontend/app.js`, `frontend/index.html`, `tests/test_frontend_static.py`.
- **Risk level:** Medium.
- **Implementation approach:** Validate generated JSON against a lightweight schema and assert required frontend fields render from a fixture.
- **Validation method:** Static/frontend tests and optional browser smoke in environments with Chromium.
- **Expected result:** API payloads remain consumable by the frontend.
- **Requires network access:** No.
- **Requires external credentials:** No.

### E4. P2 — Add reproducibility and artifact hash tests for synthetic workflow

- **Problem:** Reproducibility claims require deterministic outputs across supported environments.
- **Why it matters:** Research workflows must be replayable.
- **Files likely affected:** `src/behavioral_stress/workflows/synthetic_workflow.py`, `src/behavioral_stress/utils/reproducibility.py`, `tests/test_workflow.py`, `tests/test_synthetic.py`.
- **Risk level:** Medium.
- **Implementation approach:** Pin deterministic seeds and compare stable artifact metadata or normalized hashes while avoiding brittle timestamp fields.
- **Validation method:** Run synthetic workflow twice and compare normalized outputs.
- **Expected result:** Synthetic outputs are deterministic within documented tolerances.
- **Requires network access:** No.
- **Requires external credentials:** No.

### E5. P2 — Add opt-in live provider integration tests

- **Problem:** Live Google Trends behavior cannot be validated by offline tests and is currently unvalidated.
- **Why it matters:** Provider APIs can change, throttle, or rescale data.
- **Files likely affected:** `tests/test_google_trends_ingestion.py`, possible new `tests/integration/`, `src/behavioral_stress/ingestion/trends.py`, docs.
- **Risk level:** Medium.
- **Implementation approach:** Add explicitly marked tests requiring environment variables such as `RUN_LIVE_TRENDS_TESTS=1`. Keep them out of default CI.
- **Validation method:** Run live tests manually or in scheduled networked CI.
- **Expected result:** Live ingestion has a non-blocking validation path.
- **Requires network access:** Yes.
- **Requires external credentials:** No for public Google Trends access, subject to provider behavior.

## F. Production hardening gaps

### F1. P1 — Add persistent alert history design before implementation

- **Problem:** Alert history is process-local and disappears on restart.
- **Why it matters:** Cooldowns, duplicate suppression, and audit trails cannot survive deployments.
- **Files likely affected:** `src/behavioral_stress/alerting/engine.py`, `src/behavioral_stress/alerting/geo.py`, docs under `docs/operations/`, future tests.
- **Risk level:** High if implemented without design; medium as planning work.
- **Implementation approach:** Define an interface for durable alert history and replay semantics before selecting a backend. Keep in-memory implementation as default for offline demos.
- **Validation method:** Interface tests using a temporary file or in-memory fake; future restart simulation tests.
- **Expected result:** A migration path exists without forcing production infrastructure into the prototype.
- **Requires network access:** No for file-backed tests; backend-specific options may vary later.
- **Requires external credentials:** No for local file/SQLite; yes for managed stores if introduced later.

### F2. P2 — Enforce API auth only when production mode is enabled

- **Problem:** Production experimental config lists an API token secret, but the API server does not enforce auth.
- **Why it matters:** Users may assume the dashboard API is protected when it is not.
- **Files likely affected:** `src/behavioral_stress/api/server.py`, `configs/production.experimental.yaml`, `docs/production_hardening.md`, `tests/test_ops_hardening.py`.
- **Risk level:** Medium.
- **Implementation approach:** First document current unauthenticated demo status. If adding enforcement, gate it by explicit production mode and keep local demo friction low.
- **Validation method:** Tests for unauthenticated demo mode and rejected unauthenticated production-mode requests.
- **Expected result:** Security posture is explicit and testable.
- **Requires network access:** No.
- **Requires external credentials:** No for tests; yes for real deployment secret management.

### F3. P2 — Strengthen healthcheck and degraded-state semantics

- **Problem:** Healthcheck currently treats `ok` and `degraded` as acceptable for demo behavior, which is weak for production gating.
- **Why it matters:** Deployment automation needs a stricter signal than demo availability.
- **Files likely affected:** `src/behavioral_stress/ops/health.py`, `scripts/healthcheck.py`, `docker/docker-compose.yml`, `docs/operations/deployment.md`.
- **Risk level:** Medium.
- **Implementation approach:** Preserve demo health behavior but add a stricter production/readiness mode that fails on degraded dependencies.
- **Validation method:** Unit tests for `ok`, `degraded`, and failure modes; Docker healthcheck smoke.
- **Expected result:** Operators can choose demo liveness or production readiness behavior explicitly.
- **Requires network access:** No.
- **Requires external credentials:** No.

### F4. P2 — Add secret redaction and no-credential regression checks

- **Problem:** Security tests for secret redaction and committed credentials are listed as needed.
- **Why it matters:** Even research prototypes should not leak API tokens or deployment secrets.
- **Files likely affected:** `src/behavioral_stress/ops/structured_logging.py`, `src/behavioral_stress/ops/environment.py`, `tests/test_ops_hardening.py`, docs.
- **Risk level:** Low to medium.
- **Implementation approach:** Add redaction helpers and tests over representative config/env fields. Add repository scan checks for known secret variable names but avoid brittle high-false-positive scans.
- **Validation method:** Unit tests for redaction; optional pre-commit or CI secret scan.
- **Expected result:** Logs and diagnostics do not expose configured secrets.
- **Requires network access:** No.
- **Requires external credentials:** No.

## G. Research validation gaps

### G1. P2 — Add explicit synthetic-only validation boundary

- **Problem:** Current validation is synthetic-only and no prospective real-data validation exists.
- **Why it matters:** Scientific claims must not exceed evidence.
- **Files likely affected:** `README.md`, `docs/reproducibility/reproducibility_guide.md`, `notebooks/04_validation_plan.ipynb`, `src/behavioral_stress/validation/synthetic_validation.py`.
- **Risk level:** Medium.
- **Implementation approach:** Label metrics as synthetic validation unless backed by real data. Add a validation-readiness checklist rather than claiming predictive value.
- **Validation method:** Documentation review and tests that output metadata includes `synthetic_only` or equivalent flag.
- **Expected result:** Research claims remain conservative and evidence-aligned.
- **Requires network access:** No.
- **Requires external credentials:** No.

### G2. P2 — Plan calibration and uncertainty validation before implementing richer BSI

- **Problem:** Design calls for calibrated uncertainty and confidence, but implementation uses simpler penalties and bounded weighted composites.
- **Why it matters:** Incorrect uncertainty can be worse than no uncertainty for decision support.
- **Files likely affected:** `BSI_DESIGN.md`, `src/behavioral_stress/alerting/bsi.py`, `src/behavioral_stress/validation/metrics.py`, future tests.
- **Risk level:** High if rushed; medium as research planning.
- **Implementation approach:** Define calibration datasets, holdout periods, metrics, and acceptance criteria before adding confidence claims. Keep current BSI labeled MVP until validated.
- **Validation method:** Future calibration notebooks/tests with documented data provenance.
- **Expected result:** Uncertainty work proceeds with measurable criteria rather than cosmetic fields.
- **Requires network access:** Likely yes for real external datasets.
- **Requires external credentials:** Possibly, depending on data sources.

### G3. P3 — Add confounder and false-positive evaluation framework

- **Problem:** Alert suppressions do not cover news shocks, holidays, viral topics, seasonality, or local events.
- **Why it matters:** Behavioral search signals are highly confounded; alert quality depends on reducing false positives.
- **Files likely affected:** `src/behavioral_stress/alerting/engine.py`, `src/behavioral_stress/causal/event_study.py`, `src/behavioral_stress/causal/negative_controls.py`, `src/behavioral_stress/validation/ablation.py`, future datasets.
- **Risk level:** High research complexity.
- **Implementation approach:** Start with offline confounder flags and negative controls. Avoid automatically suppressing alerts from live news until validated.
- **Validation method:** Backtests with labeled event windows and negative controls.
- **Expected result:** False-positive behavior can be measured and improved over time.
- **Requires network access:** Likely for external event/news/calendar data unless fixtures are curated locally.
- **Requires external credentials:** Possibly, depending on providers.

### G4. P3 — Validate geography/provider coverage and low-volume behavior

- **Problem:** Geo metadata exists, but provider code support and low-volume behavior are manual/unvalidated.
- **Why it matters:** Geographic comparisons can be misleading when provider availability and sampling vary.
- **Files likely affected:** `src/behavioral_stress/keywords/registry.py`, `src/behavioral_stress/ingestion/trends.py`, `src/behavioral_stress/alerting/geo.py`, `configs/ingestion/google_trends_sample.yaml`.
- **Risk level:** Medium.
- **Implementation approach:** Add explicit provider-support checks and store support status in metadata. Use opt-in live validation for provider support.
- **Validation method:** Offline metadata tests plus live provider support checks behind opt-in marker.
- **Expected result:** Unsupported or low-volume geographies are flagged before scoring/alerting.
- **Requires network access:** Yes for live provider validation.
- **Requires external credentials:** No for public Google Trends access, subject to provider behavior.

## H. UI/dashboard gaps

### H1. P1 — Add dashboard demo-mode labeling and metadata display

- **Problem:** The Chrome-friendly dashboard is usable but mostly a synthetic artifact viewer.
- **Why it matters:** Users need visible context that the payload is synthetic/demo data.
- **Files likely affected:** `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `src/behavioral_stress/api/dashboard_data.py`, `tests/test_frontend_static.py`.
- **Risk level:** Low.
- **Implementation approach:** Surface payload metadata such as `mode`, `synthetic_only`, generation timestamp, and validation status. Keep UI simple.
- **Validation method:** Static frontend tests assert metadata text is present for synthetic payloads.
- **Expected result:** Dashboard does not overstate validity.
- **Requires network access:** No.
- **Requires external credentials:** No.

### H2. P1 — Make dashboard selectors either filter data or clearly state they are placeholders

- **Problem:** Selectors mostly update dropdown state and rerender the same synthetic payload rather than filtering by selected geography.
- **Why it matters:** Non-functional controls reduce trust and can confuse validation.
- **Files likely affected:** `frontend/app.js`, `frontend/index.html`, `tests/test_frontend_static.py`.
- **Risk level:** Medium.
- **Implementation approach:** Prefer minimal real filtering if the payload supports it; otherwise label controls as demo selectors until schema work is complete.
- **Validation method:** Frontend tests assert selected geography changes visible chart/table data or shows placeholder status.
- **Expected result:** UI behavior is honest and testable.
- **Requires network access:** No.
- **Requires external credentials:** No.

### H3. P1 — Add report rendering from `ReportGenerator` outputs

- **Problem:** Frontend displays demo report data rather than structured or Markdown output from the report generator.
- **Why it matters:** Report output is part of the required end-to-end path and should not be a separate mock forever.
- **Files likely affected:** `src/behavioral_stress/alerting/reporting.py`, `src/behavioral_stress/api/dashboard_data.py`, `frontend/app.js`, `tests/test_frontend_static.py`.
- **Risk level:** Medium.
- **Implementation approach:** Convert report generator output into a sanitized JSON payload field and display it in a simple report panel. Preserve demo warnings.
- **Validation method:** Golden payload fixture and static frontend smoke.
- **Expected result:** Dashboard can display the same report object produced by the backend path.
- **Requires network access:** No.
- **Requires external credentials:** No.

### H4. P2 — Add optional browser e2e smoke test

- **Problem:** Browser behavior beyond static-file checks is not validated unless a real browser/e2e environment is used.
- **Why it matters:** Chart rendering, selector behavior, and export buttons can break outside unit/static tests.
- **Files likely affected:** `tests/test_frontend_static.py`, possible new browser test config, `frontend/app.js`.
- **Risk level:** Low to medium.
- **Implementation approach:** Add an optional Chromium/Chrome smoke test skipped when browser tooling is absent. Keep default CI offline-friendly.
- **Validation method:** Load static dashboard, assert no console errors for core path, verify chart/table/report sections render.
- **Expected result:** Frontend has a stronger validation path without making all environments depend on browser tooling.
- **Requires network access:** No after browser dependencies are installed; yes if installing browser tooling in CI.
- **Requires external credentials:** No.

## Suggested execution order

1. **P0 correctness:** A1, E1, B1, C1, A2, A3.
2. **P1 minimal end-to-end coherence:** D1, D2, A4, E2, E3, H1, H2, H3, B2.
3. **P1/P2 reproducibility and deployment clarity:** D3, E4, B3, F1, F2, F3, F4.
4. **P2/P3 research validation:** G1, G2, G3, G4, E5, H4.

## Explicit non-goals for the first fix cycle

- Do not claim real-world predictive validity.
- Do not introduce live provider requirements into default tests.
- Do not replace the current architecture with a new orchestration framework.
- Do not add production infrastructure such as managed databases, queues, auth gateways, or secret managers before interfaces and tests justify them.
- Do not expand the UI with new features until current controls, schema, and warnings are correct.
