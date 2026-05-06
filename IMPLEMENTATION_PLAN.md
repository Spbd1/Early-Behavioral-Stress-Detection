# Executable Implementation Plan

This plan converts `FINALIZATION_CHECKLIST.md` and `ROADMAP.md` into implementation milestones. It intentionally does **not** implement production behavior yet. Each milestone is scoped to be independently testable, to end in a working repository state, and to move from governance and data foundations toward advanced modeling and alerting.

## Planning principles

- **Working state at every merge:** existing synthetic demos and tests must continue to run unless a milestone explicitly replaces them with equivalent real-data-safe behavior.
- **No external alerts before evidence:** alert delivery is blocked until data quality, decision-time backtesting, calibration, and human review gates are complete.
- **No silent mutation of evidence:** raw source responses, feature snapshots, model artifacts, predictions, and alert records are immutable or versioned.
- **Human approval for risky changes:** keyword promotion, threshold promotion, model promotion, and external reports require review metadata.
- **Synthetic evidence is not launch evidence:** synthetic tests remain useful for unit coverage and regression testing, but not for production readiness claims.

## Milestone categories

### Must-have production requirements

These milestones are required before the system can be called an experimental production platform.

| ID | Milestone | Primary gate/phase coverage | Working-state definition |
|---|---|---|---|
| P0 | Governance, scope, and prototype boundary freeze | Checklist Gate 0; Roadmap Phase 0 | Repository clearly separates prototype/demo behavior from governed experimental operation. |
| P1 | Source registry, contracts, and local storage foundation | Checklist Gates 1-2; Roadmap Phase 1 | Offline contract tests validate source metadata, schemas, quality checks, and immutable storage semantics. |
| P2 | Connector interface and Google Trends ingestion | Checklist Gate 1; Roadmap Phase 2 | Recorded fixtures can be parsed, validated, persisted, and replayed without live network calls. |
| P3 | Curated features, transform registry, and feature snapshots | Checklist Gates 2-3; Roadmap Phase 4 | Reproducible feature snapshots are generated from immutable raw/curated data with persisted transform parameters. |
| P4 | Experiment tracking and model registry foundation | Checklist Gate 5; Roadmap Phase 4 | Model training runs produce auditable artifacts and registry entries without changing production state. |
| P5 | Decision-time validation, baselines, and calibration governance | Checklist Gates 5-6; Roadmap Phase 5 | Backtests use only information available at each simulated date and produce comparable validation/calibration reports. |
| P6 | Shadow-mode inference and drift monitoring | Checklist Gates 7-8; Roadmap Phases 6-7 | Scheduled or manually triggered shadow runs create predictions, drift status, and internal reports without external alerts. |
| P7 | Human-reviewed experimental alert workflow | Checklist Gates 0, 5, 7-8; Roadmap Phase 6 | Alerts require data-quality pass, calibrated thresholds, persistence rules, and reviewer approval before delivery. |
| P8 | Security, deployment, and operational hardening | Checklist Gates 8-9; Roadmap Phases 7-8 | Deployment, rollback, observability, access control, and CI/CD controls are tested and documented. |

### Research enhancements

These milestones improve scientific credibility and robustness after the must-have foundations are in place.

| ID | Milestone | Primary gate/phase coverage | Working-state definition |
|---|---|---|---|
| R1 | Governed ontology and LLM keyword workflow | Checklist Gate 4; Roadmap Phase 3 | Candidate keywords are proposed, filtered, reviewed, validated, and versioned before ingestion. |
| R2 | Multi-source and multi-region research panels | Checklist Gates 1, 3, 6; Roadmap Phases 2, 5, 8 | Experiments can compare regions and source families while preserving lineage and contracts. |
| R3 | Robustness, placebo, and negative-control evidence pack | Checklist Gate 6; Roadmap Phase 5 | Validation artifacts include sensitivity, negative-control, placebo, and source-outage analyses. |
| R4 | Advanced model comparison automation | Checklist Gates 5-6; Roadmap Phases 5, 8 | Adaptive HMMs are compared against baselines and alternative models using reproducible registry-backed runs. |

### Optional experimental features

These are non-blocking and should not precede the must-have milestones they depend on.

| ID | Milestone | Primary gate/phase coverage | Working-state definition |
|---|---|---|---|
| X1 | Interactive research dashboard extensions | Checklist Gate 8; Roadmap Phase 7 | Dashboard reads versioned artifacts and cannot mutate models, thresholds, or alert state. |
| X2 | Cost and performance simulation harness | Checklist Gate 9; Roadmap Phase 8 | Load/cost estimates are generated from planned keyword/source volumes without production dependencies. |
| X3 | Automated periodic independent review package | Checklist Gates 6, 8; Roadmap Phase 8 | A reproducible bundle supports external or independent scientific review. |

---

## Must-have production milestones

### P0 — Governance, scope, and prototype boundary freeze

**Objective**

Define the intended operating mode, responsible-use boundaries, and prototype/demo limitations before adding real-data or alerting capabilities.

**Files to modify**

- `README.md`
- `FINALIZATION_CHECKLIST.md`
- `ROADMAP.md`
- `ARCHITECTURE_GAPS.md`
- `REPAIR_CHECKLIST.md`
- `docs/product_scope.md` *(new)*
- `docs/responsible_use_policy.md` *(new)*
- `docs/risk_register.md` *(new)*
- `docs/prototype_inventory.md` *(new)*
- Demo/report text in `src/behavioral_stress/visualization/`, `langflow/`, and `notebooks/` only where labels are surfaced.

**Risks**

- Ambiguous scope could allow users to interpret synthetic demos as validated recession or diagnostic predictions.
- Responsible-use language may be too broad to guide engineering decisions.
- Prototype inventory can become stale unless maintained with CI or review checklist updates.

**Validation criteria**

- Documentation identifies intended users, allowed uses, prohibited uses, geographies, cadence, alert recipients, and launch restrictions.
- All public demo/report surfaces state synthetic-only limitations until real-data gates pass.
- Risk register covers false alarms, missed events, source outages, source drift, public misinterpretation, and model misuse.
- A repository search confirms no unsupported production-readiness or individual-diagnostic claims remain.

**Expected outputs**

- Product/research scope document.
- Responsible-use policy.
- Risk register with owners and mitigations.
- Maintained prototype/stub inventory.
- Updated checklist statuses for completed governance artifacts.

**Rollback considerations**

- Documentation-only rollback is safe, but reverting must not remove existing safety disclaimers.
- If language is disputed, revert to the last conservative policy and block downstream production milestones until resolved.

---

### P1 — Source registry, contracts, and local storage foundation

**Objective**

Create the data governance and storage primitives needed before integrating live sources: source metadata, schema contracts, immutable raw landing, curated time-series structure, and data-quality status.

**Files to modify**

- `src/behavioral_stress/data/ingestion.py`
- `src/behavioral_stress/data/preprocessing.py`
- `src/behavioral_stress/utils/config.py`
- `configs/default.yaml`
- `configs/validation.yaml`
- `data/README.md`
- `tests/` for contract, quality, and storage behavior.
- `docs/data_contracts.md` *(new)*
- `docs/source_registry.md` *(new or generated from config)*
- `docs/data_retention.md` *(new)*
- `src/behavioral_stress/data/contracts.py` *(new)*
- `src/behavioral_stress/data/storage.py` *(new)*
- `src/behavioral_stress/data/quality.py` *(new)*

**Risks**

- Overengineering storage before source behavior is known.
- Under-specifying lineage fields and needing migration after real ingestion begins.
- Treating local filesystem layout as final production architecture.

**Validation criteria**

- Contract tests reject invalid timestamps, missing required columns, duplicate rows, unsupported frequencies, nulls where disallowed, invalid ranges, and missing source metadata.
- Raw storage writes are append-only and content-addressed or hash-verified.
- Curated records retain lineage back to raw source snapshots.
- Quality checks emit machine-readable pass/warn/fail states for freshness, completeness, gaps, unexpected zeroes, source revisions, and distribution shifts.
- Backfill/replay tests prove raw evidence is not overwritten.

**Expected outputs**

- Source registry schema and at least one placeholder-approved source record.
- Data contract classes/functions and tests.
- Local raw/curated artifact layout documented in `data/README.md`.
- Data quality result schema.
- Retention, archival, and deletion policy documentation.

**Rollback considerations**

- Keep migrations idempotent and reversible while no production data exists.
- If a storage abstraction is flawed, preserve raw fixture files and registry metadata before refactoring.
- Never rollback by deleting raw evidence once live ingestion exists; instead deprecate paths through metadata.

---

### P2 — Connector interface and Google Trends ingestion

**Objective**

Implement a typed public-signal connector interface and a Google Trends connector that can fetch, normalize, validate, persist, and replay data with recorded fixtures and no live-network dependency in tests.

**Files to modify**

- `src/behavioral_stress/data/ingestion.py`
- `src/behavioral_stress/data/contracts.py`
- `src/behavioral_stress/data/storage.py`
- `src/behavioral_stress/data/quality.py`
- `configs/default.yaml`
- `configs/validation.yaml`
- `data/README.md`
- `tests/` for connector fixture, retry/backoff, parsing, outage, and replay coverage.
- `src/behavioral_stress/data/connectors/base.py` *(new)*
- `src/behavioral_stress/data/connectors/google_trends.py` *(new)*
- `tests/fixtures/google_trends/` *(new)*
- `docs/source_registry.md`

**Risks**

- Google Trends normalization can be misinterpreted as absolute search volume.
- Rate limits and response changes may cause brittle ingestion.
- Live-source tests can become flaky if fixtures are not enforced.
- Terms-of-service limitations may constrain automated collection.

**Validation criteria**

- Connector interface has typed fetch, normalize, validate, persist, and replay paths.
- Google Trends query batching supports region, category, and time-window parameters.
- Rate limiting, retries, and exponential backoff are covered by deterministic tests.
- Every run records query parameters, collection timestamp, response hash, data vintage, connector version, and source ID.
- Fixture tests run without network calls.
- Partial-load and source-outage tests either block downstream use or annotate data-quality status.

**Expected outputs**

- Connector base interface.
- Google Trends connector with documented normalization caveats.
- Recorded fixture corpus.
- Reproducible local ingestion command or test helper.
- Updated source registry with owner, endpoint, terms/license, quota, cadence, revision behavior, geography, and allowed use.

**Rollback considerations**

- Disable the connector through configuration rather than deleting registry history.
- Preserve raw responses and connector version metadata for auditability.
- If terms review fails, quarantine the connector and keep fixture-only tests for interface validation.

---

### P3 — Curated features, transform registry, and feature snapshots

**Objective**

Build a reproducible preprocessing and feature-generation path that persists train-time transform parameters and emits immutable model-input snapshots with enforced schema and lineage.

**Files to modify**

- `src/behavioral_stress/data/preprocessing.py`
- `src/behavioral_stress/data/storage.py`
- `src/behavioral_stress/data/quality.py`
- `src/behavioral_stress/utils/reproducibility.py`
- `configs/default.yaml`
- `configs/validation.yaml`
- `tests/` for transform persistence, leakage, schema ordering, missing data, and snapshot immutability.
- `src/behavioral_stress/features/` *(new package)*
- `src/behavioral_stress/features/transforms.py` *(new)*
- `src/behavioral_stress/features/snapshots.py` *(new)*
- `docs/features.md` *(new)*

**Risks**

- Feature leakage from future data in historical transforms.
- Inconsistent column ordering between training and inference.
- Silent clipping of outliers without provenance.
- Missing-data behavior can differ by source and bias downstream models.

**Validation criteria**

- Transform registry persists parameters from training and reuses them during inference.
- Feature schema and column order are enforced before model calls.
- Missing-data policy is encoded per source and feature family.
- Publication lag, timezone, frequency alignment, calendar/holiday, and revision semantics are represented in contracts or feature metadata.
- Leakage tests prove future observations are excluded from historical transforms and validation folds.
- Feature snapshots are immutable, addressable by ID, and include source, ontology node, transform version, and validation status.

**Expected outputs**

- Transform registry.
- Feature snapshot writer/reader.
- Feature schema documentation.
- Leakage regression tests.
- Updated preprocessing behavior that remains compatible with existing synthetic tests.

**Rollback considerations**

- Maintain backward compatibility shims for prototype preprocessing until callers migrate.
- Feature snapshots should be versioned; rollback selects a previous snapshot rather than mutating current artifacts.
- If leakage is discovered, invalidate affected snapshots and validation reports through metadata.

---

### P4 — Experiment tracking and model registry foundation

**Objective**

Make modeling runs reproducible and auditable by recording dataset IDs, feature schemas, transform IDs, config hashes, git commits, dependency locks, random seeds, diagnostics, validation reports, and model lifecycle state.

**Files to modify**

- `src/behavioral_stress/models/adaptive_hmm.py`
- `src/behavioral_stress/models/baselines.py`
- `src/behavioral_stress/models/emissions.py`
- `src/behavioral_stress/utils/reproducibility.py`
- `configs/default.yaml`
- `pyproject.toml`
- `requirements.txt`
- `tests/` for artifact metadata, registry transitions, diagnostics, and rollback.
- `src/behavioral_stress/experiments/tracking.py` *(new)*
- `src/behavioral_stress/models/registry.py` *(new)*
- `docs/model_registry.md` *(new)*

**Risks**

- Registry state changes can be treated as approval without human review.
- HMM state labels can swap across retraining runs if mapping is not stabilized.
- Non-finite values or convergence failures can be hidden by successful artifact writes.

**Validation criteria**

- Training produces model artifacts with feature schema, transform ID, training dataset ID, config hash, git commit, dependency lock, seed, and validation report path.
- Registry supports candidate, staging, production, archived, and rollback metadata while requiring approval metadata for promotion.
- Diagnostics cover convergence, non-finite values, likelihood trends, posterior entropy, state occupancy, transition stability, and sensitivity to training windows.
- State-label mapping is documented and tested for stable interpretation.
- Existing synthetic model tests continue to pass.

**Expected outputs**

- Experiment tracking module.
- Model registry module.
- HMM artifact schema.
- Baseline artifact schema.
- Model diagnostics report template.

**Rollback considerations**

- A failed registry migration must leave existing candidate artifacts readable.
- Production/staging pointer rollback should be metadata-only and auditable.
- Never overwrite model artifacts; archive superseded models instead.

---

### P5 — Decision-time validation, baselines, and calibration governance

**Objective**

Create real-world validation evidence before operational use: event catalogs, decision-time backtests, baseline comparisons, calibration reports, robustness checks, and statistical review gates.

**Files to modify**

- `src/behavioral_stress/validation/rolling_origin.py`
- `src/behavioral_stress/validation/metrics.py`
- `src/behavioral_stress/validation/ablation.py`
- `src/behavioral_stress/models/baselines.py`
- `scripts/run_validation.py`
- `configs/validation.yaml`
- `tests/` for event catalog, decision-time backtests, baselines, calibration, and robustness.
- `src/behavioral_stress/validation/events.py` *(new)*
- `src/behavioral_stress/validation/backtesting.py` *(new)*
- `src/behavioral_stress/validation/calibration.py` *(new)*
- `docs/validation_governance.md` *(new)*

**Risks**

- Accidentally using revised or future data in historical simulations.
- Optimizing thresholds to historical events without accounting for false alarms and uncertainty.
- Overclaiming causal or macroeconomic predictive power.
- Baselines may outperform advanced models, requiring scope or model changes.

**Validation criteria**

- Event catalog records definitions, dates, vintages, label uncertainty, embargoes, and owners.
- Backtests only use data available as of each simulated date.
- Baseline suite includes static HMM, naive persistence, change-point, macro lag, and classifier baselines where feasible.
- Calibration reports document false-alarm/lead-time tradeoffs, uncertainty intervals, and threshold review status.
- Robustness checks cover geography, frequency, keyword family, source outage, placebo, and negative controls.
- Statistical review approval is required before any model or threshold can generate operational alerts.

**Expected outputs**

- Versioned event/target catalog.
- Decision-time backtesting harness.
- Baseline comparison report.
- Calibration report template and generated sample artifact.
- Statistical review gate documentation.

**Rollback considerations**

- If leakage or target-definition errors are found, mark affected validation artifacts invalid instead of editing them in place.
- Threshold rollback returns to the last reviewed threshold set or disables alerts.
- Keep prior baseline results for audit comparisons.

---

### P6 — Shadow-mode inference and drift monitoring

**Objective**

Run live or scheduled ingestion and inference internally without external alerts, with drift monitoring, operational logs, dashboards, reports, and runbooks.

**Files to modify**

- `src/behavioral_stress/workflows/`
- `src/behavioral_stress/utils/logging.py`
- `src/behavioral_stress/visualization/dashboard.py`
- `scripts/`
- `configs/default.yaml`
- `docker/docker-compose.yml`
- `tests/` for scheduler, idempotent inference, drift monitor, report generation, and failure handling.
- `src/behavioral_stress/inference/job.py` *(new)*
- `src/behavioral_stress/monitoring/drift.py` *(new)*
- `src/behavioral_stress/reporting/internal_reports.py` *(new)*
- `docs/runbooks/` *(new)*
- `docs/operations.md` *(new)*

**Risks**

- Shadow-mode outputs may be mistaken for external alerts.
- Scheduler failures can silently create stale or partial data.
- Drift monitors can be noisy before enough real operating history exists.

**Validation criteria**

- Inference is idempotent, versioned, replayable, and blocked or annotated on failed data-quality checks.
- Drift monitors cover source freshness, feature distribution, posterior entropy, state occupancy, likelihood, and transition stability.
- Structured logs include run_id, dataset_id, model_id, source_id, alert_id where applicable, and severity.
- Internal reports include model/data versions, caveats, uncertainty, drivers, drift status, and responsible-use text.
- Dashboards show data freshness, job health, model health, drift, and shadow alert status.
- Runbooks cover stale sources, failed DAGs, model collapse, false alerts, and rollback.

**Expected outputs**

- Shadow inference job.
- Prediction store or artifact output.
- Drift monitor results.
- Internal-only report generator.
- Operational dashboard updates.
- Incident runbooks and SLO draft.

**Rollback considerations**

- Disable scheduled jobs through configuration while preserving last successful run artifacts.
- Repoint inference to a previous approved model or suspend inference if data-quality status fails.
- Dashboard rollback must not delete historical monitoring records.

---

### P7 — Human-reviewed experimental alert workflow

**Objective**

Add cautious experimental alert generation with calibrated operating points, uncertainty and data-quality gates, suppression, acknowledgement, reviewer approval, delivery tracking, and postmortem metadata.

**Files to modify**

- `src/behavioral_stress/inference/job.py`
- `src/behavioral_stress/monitoring/drift.py`
- `src/behavioral_stress/reporting/internal_reports.py`
- `src/behavioral_stress/visualization/dashboard.py`
- `configs/default.yaml`
- `configs/validation.yaml`
- `tests/` for alert rule evaluation, review workflow, audit fields, suppression, and blocked delivery.
- `src/behavioral_stress/alerts/rules.py` *(new)*
- `src/behavioral_stress/alerts/review.py` *(new)*
- `src/behavioral_stress/alerts/audit.py` *(new)*
- `docs/alerting_policy.md` *(new)*

**Risks**

- False alarms can damage trust or cause public misinterpretation.
- Missed events can create false confidence.
- Reviewer workflow can become a rubber stamp if audit fields are weak.
- Alert text may imply causal, diagnostic, or recession-prediction claims beyond evidence.

**Validation criteria**

- Alert rules use persistence, uncertainty, suppression, severity, and data-quality annotations.
- External alert/report delivery is blocked without reviewer approval.
- Audit records include score, threshold, data status, model ID, reviewer, delivery status, acknowledgement, suppression status, and postmortem fields.
- Alert reports include caveats, responsible-use text, model/data versions, drift status, uncertainty, and major drivers.
- False-positive and missed-event review processes are documented and tested with sample records.

**Expected outputs**

- Alert rule engine.
- Human review queue/workflow.
- Alert audit table or artifact schema.
- Reviewed report template.
- Postmortem workflow.

**Rollback considerations**

- Default rollback disables external alert delivery while preserving internal shadow inference.
- Threshold rollback returns to the last approved threshold set or to no-alert mode.
- Faulty alerts are corrected through postmortem records, not deletion.

---

### P8 — Security, deployment, and operational hardening

**Objective**

Harden the platform for controlled experimental production operation with secrets handling, access controls, CI/CD, infrastructure definitions, backup/restore, rollback, load testing, observability, and operational ownership.

**Files to modify**

- `.github/workflows/` *(new or existing if present)*
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `pyproject.toml`
- `requirements.txt`
- `configs/`
- `tests/` for security-sensitive behavior, backup/restore, rollback, and smoke tests.
- `infra/` *(new)*
- `docs/deployment.md` *(new)*
- `docs/security.md` *(new)*
- `docs/backup_restore.md` *(new)*
- `docs/release_process.md` *(new)*

**Risks**

- Secrets can leak through configs, logs, notebooks, images, or artifacts.
- Access controls can be bypassed in dashboards or artifact stores.
- Incomplete rollback/restore can prolong incidents.
- CI/CD hardening can slow research iteration if not staged carefully.

**Validation criteria**

- Secrets never appear in files, logs, notebooks, images, or committed artifacts.
- Dashboards, artifacts, reports, and administrative actions require authentication and authorization in the target deployment.
- CI runs tests, lint, type checks where configured, dependency scan, container scan, and release artifact generation.
- Infrastructure is reproducible through code and reviewable before deployment.
- Backup/restore and rollback procedures are tested.
- Performance/load tests cover planned keyword/source volume with bounded latency and cost.

**Expected outputs**

- Hardened CI/CD workflows.
- Deployment and infrastructure definitions.
- Secrets and access-control documentation.
- Backup/restore test evidence.
- Release and rollback process.
- Load/cost report.

**Rollback considerations**

- Roll back deployments through versioned release artifacts and infrastructure state.
- Revoke/rotate credentials if leakage is suspected.
- Preserve audit logs and incident records even when services are rolled back.

---

## Research enhancement milestones

### R1 — Governed ontology and LLM keyword workflow

**Objective**

Safely expand ontology-guided signal panels using versioned concepts, structured LLM proposals, sensitive-term filters, human review, and keyword validation before ingestion.

**Files to modify**

- `src/behavioral_stress/ontology/ontology.py`
- `src/behavioral_stress/ontology/signal_codebook.py`
- `src/behavioral_stress/signal_discovery/`
- `configs/default.yaml`
- `tests/` for ontology versioning, filters, review state, and validation.
- `src/behavioral_stress/ontology/store.py` *(new)*
- `src/behavioral_stress/ontology/llm_prompts.py` *(new)*
- `src/behavioral_stress/ontology/review.py` *(new)*
- `src/behavioral_stress/ontology/filters.py` *(new)*
- `docs/ontology_workflow.md` *(new)*

**Risks**

- LLM-generated terms can introduce sensitive, stigmatizing, redundant, or unstable signals.
- Keyword drift can create non-stationary feature panels.
- Multiple-testing risk can inflate apparent event associations.

**Validation criteria**

- Ontology records concepts, hypotheses, inclusion/exclusion rules, language/geography scope, owner, and review status.
- Prompt templates and output schemas are versioned.
- LLM model version, prompt version, parameters, and output are logged for every proposal.
- Sensitive-term and misuse filters block unsafe terms before review.
- No keyword enters ingestion without human approval.
- Keyword validation covers stability, redundancy, source availability, drift, event association, and multiple-testing risk.
- Retirement preserves history and never silently deletes past features.

**Expected outputs**

- Versioned ontology store.
- Prompt templates and structured output schemas.
- Review queue metadata.
- Sensitive-term filter list/rules.
- Keyword validation report.

**Rollback considerations**

- Retire or quarantine problematic keywords instead of deleting them.
- Revert prompt versions through version metadata.
- Preserve rejected proposals and reviewer rationale for auditability.

---

### R2 — Multi-source and multi-region research panels

**Objective**

Extend beyond a single source or geography by adding at least one non-search source and partitioning feature snapshots by region/source family for comparative research.

**Files to modify**

- `src/behavioral_stress/data/connectors/`
- `src/behavioral_stress/features/`
- `src/behavioral_stress/validation/`
- `configs/default.yaml`
- `configs/validation.yaml`
- `tests/` for multi-source and multi-region contracts.
- `docs/source_registry.md`
- `docs/features.md`

**Risks**

- Source terms, cadence, and revision policies may be incompatible.
- Cross-region comparisons can be misleading if normalization semantics differ.
- Higher data volume increases cost and operational complexity.

**Validation criteria**

- At least one additional public aggregate signal connector passes fixture-based tests.
- Source registry includes terms, cadence, quota, geography, and revision behavior for every source.
- Feature snapshots support region/source-family partitions with lineage.
- Validation reports can compare single-source and multi-source panels.

**Expected outputs**

- Additional connector and fixtures.
- Multi-source feature panels.
- Multi-region snapshot metadata.
- Comparative validation report.

**Rollback considerations**

- Disable a problematic source or region through configuration.
- Preserve source-specific raw and curated data for audit.
- Invalidate only affected feature partitions and validation artifacts.

---

### R3 — Robustness, placebo, and negative-control evidence pack

**Objective**

Strengthen statistical evidence by packaging robustness, placebo, negative-control, source-outage, and sensitivity analyses for review.

**Files to modify**

- `src/behavioral_stress/causal/negative_controls.py`
- `src/behavioral_stress/causal/sensitivity.py`
- `src/behavioral_stress/causal/event_study.py`
- `src/behavioral_stress/validation/ablation.py`
- `src/behavioral_stress/validation/metrics.py`
- `tests/` for robustness report generation.
- `docs/validation_governance.md`

**Risks**

- Robustness tests may reveal weak evidence requiring threshold or model rollback.
- Negative controls can be misread as causal validation if documentation is imprecise.
- Evidence packs may become too heavyweight for routine iteration.

**Validation criteria**

- Report generation includes geography, frequency, keyword-family, source-outage, placebo, and negative-control checks.
- Sensitivity analyses are tied to model IDs, feature snapshot IDs, and event catalog versions.
- Statistical review can approve, reject, or request changes with recorded rationale.

**Expected outputs**

- Robustness evidence pack.
- Placebo and negative-control reports.
- Sensitivity analysis artifacts.
- Review metadata.

**Rollback considerations**

- If evidence weakens a model, demote the model or disable alerts while preserving reports.
- Keep superseded evidence packs for reproducibility.
- Update claims and report caveats before restoring any alerting behavior.

---

### R4 — Advanced model comparison automation

**Objective**

Automate fair comparisons among adaptive HMMs, static HMMs, change-point models, persistence rules, macro-lag baselines, classifiers, and future advanced models.

**Files to modify**

- `src/behavioral_stress/models/`
- `src/behavioral_stress/validation/backtesting.py`
- `src/behavioral_stress/validation/metrics.py`
- `src/behavioral_stress/experiments/tracking.py`
- `configs/validation.yaml`
- `tests/` for comparison orchestration and metric parity.
- `docs/model_registry.md`

**Risks**

- Automated comparison can encourage leaderboard overfitting.
- Advanced models can be less interpretable and harder to govern.
- Non-identical data windows or transforms can make comparisons invalid.

**Validation criteria**

- Every compared model uses the same approved feature snapshot and event catalog unless explicitly documented.
- Comparison reports include uncertainty, lead-time/false-alarm tradeoffs, diagnostics, and complexity notes.
- Registry records rejected, archived, and promoted candidates with rationale.

**Expected outputs**

- Model comparison runner.
- Standardized metrics table.
- Comparison report artifacts.
- Registry-backed promotion recommendations.

**Rollback considerations**

- Demote models through registry metadata rather than deleting artifacts.
- Re-run comparisons if shared snapshots or event catalogs are invalidated.
- Keep a simple baseline as fallback for shadow-mode operation.

---

## Optional experimental milestones

### X1 — Interactive research dashboard extensions

**Objective**

Enhance dashboards for internal research exploration while keeping them read-only with respect to production artifacts, thresholds, and alert state.

**Files to modify**

- `src/behavioral_stress/visualization/dashboard.py`
- `src/behavioral_stress/visualization/plots.py`
- `scripts/build_dashboard.py`
- `tests/test_workflow.py` or dashboard-specific tests.
- `docs/operations.md`

**Risks**

- Interactive controls can be mistaken for operational controls.
- Dashboard state can diverge from versioned artifact state.
- Sensitive or pre-review results may be exposed to unintended users.

**Validation criteria**

- Dashboard is read-only for production artifacts.
- All displayed results cite model ID, dataset ID, feature snapshot ID, validation state, and caveats.
- Access controls are enforced if deployed beyond local research use.

**Expected outputs**

- Read-only dashboard panels.
- Artifact-linked plots.
- Dashboard smoke tests.

**Rollback considerations**

- Disable dashboard routes or panels without changing underlying artifacts.
- Revert to static internal reports if access control is insufficient.

---

### X2 — Cost and performance simulation harness

**Objective**

Estimate scaling behavior, source/API cost, storage growth, and runtime latency for planned keyword/source/region volumes.

**Files to modify**

- `scripts/`
- `configs/default.yaml`
- `tests/` for deterministic simulation outputs.
- `src/behavioral_stress/operations/costing.py` *(new)*
- `docs/performance_and_cost.md` *(new)*

**Risks**

- Simulated costs can differ from live provider behavior.
- Performance assumptions may hide scheduler or network bottlenecks.
- Cost optimization can conflict with data completeness.

**Validation criteria**

- Simulation accepts keyword, source, region, cadence, and retention parameters.
- Output includes estimated API calls, storage volume, runtime, and cost bands.
- Load test plan defines thresholds for acceptable latency and failure rates.

**Expected outputs**

- Cost/performance simulator.
- Load-test configuration.
- Cost report artifact.

**Rollback considerations**

- The harness is non-production; rollback simply removes generated reports or disables the script.
- Do not use simulation output to override observed production SLOs.

---

### X3 — Automated periodic independent review package

**Objective**

Generate reproducible evidence bundles for periodic independent scientific or governance review.

**Files to modify**

- `scripts/`
- `src/behavioral_stress/validation/`
- `src/behavioral_stress/reporting/`
- `docs/validation_governance.md`
- `docs/release_process.md`
- `tests/` for bundle manifest generation.

**Risks**

- Review packages can expose sensitive operational details if access controls are weak.
- Bundles may omit context needed to reproduce results.
- Automated packaging can create false confidence without actual reviewer sign-off.

**Validation criteria**

- Bundle manifest lists source registry version, data snapshots, feature snapshots, model IDs, validation reports, calibration reports, alert audit summaries, and caveats.
- Reproduction instructions are included.
- Reviewer sign-off remains a separate human action.

**Expected outputs**

- Review bundle generator.
- Manifest schema.
- Reproduction instructions.
- Review checklist.

**Rollback considerations**

- Disable bundle publication if access review fails.
- Preserve generated bundle manifests for audit.
- Correct bundles through superseding versions rather than mutation.

---

## Sequencing and dependency map

```text
P0 Governance and boundaries
  -> P1 Source registry/contracts/storage
  -> P2 Connector interface + Google Trends ingestion
  -> P3 Curated features + transform registry + snapshots
  -> P4 Experiment tracking + model registry
  -> P5 Decision-time validation + calibration governance
  -> P6 Shadow-mode inference + drift monitoring
  -> P7 Human-reviewed experimental alerts
  -> P8 Security/deployment/operations hardening
```

Research enhancements should be sequenced as follows:

```text
R1 Governed ontology workflow: after P0; promotion into ingestion requires P2-P3.
R2 Multi-source/multi-region panels: after P1-P3; validation requires P5.
R3 Robustness evidence pack: after P5; can inform P7 alert decisions.
R4 Advanced model comparison: after P4-P5; can inform P6-P7 model promotion.
```

Optional experiments should be sequenced as follows:

```text
X1 Dashboard extensions: after P6 foundations; access controls require P8 before broader deployment.
X2 Cost/performance simulation: after P2-P3 for realistic volumes; before large-scale P8 deployment.
X3 Independent review package: after P5; most useful after P7 alert audit data exists.
```

## Experimental production/frontend hardening update

Completed additions for experimental production usage:

- Docker runtime hardening with non-root execution, healthcheck command, dashboard service, and `.dockerignore`.
- Runtime environment/config validation, deterministic seed enforcement, structured JSON logging, monitoring hooks, data lineage manifests, and derived model-version IDs.
- CI workflow for install, health checks, tests, deterministic synthetic smoke run, frontend payload generation, and Docker build.
- Chrome-friendly browser dashboard with conservative experimental labels, location/time/keyword filters, BSI chart, HMM posterior chart, alert timeline, top signals, geo comparison, report viewer, warnings, and export.
- Validation guardrails for schema checks, temporal leakage detection, geo-data validation, alert backtesting, and report snapshots.
- Deployment docs, operational playbooks, troubleshooting guide, reproducibility guide, and explicit reliability/production-safety risk register.

Remaining roadmap items:

- Prospective real-world validation with strict point-in-time data contracts.
- Formal model-risk review, privacy/legal review, and incident response ownership before any non-research deployment.
- Orchestrator-enforced rollback automation and monitored production telemetry integrations.
- Stronger statistical drift tests, calibrated alert thresholds, and independent audit of geographic comparability.
