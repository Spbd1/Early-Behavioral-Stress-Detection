# Finalization Checklist

This checklist defines gates for transforming the repository from a synthetic research prototype into a working experimental production-grade behavioral stress detection platform. A gate should be marked complete only when there is code, configuration, tests, documentation, and operational evidence. Synthetic-only demonstrations do not satisfy real-data gates.

## Status legend

- `[ ]` Not started or not evidenced in the repository.
- `[~]` Partially implemented or prototype-only.
- `[x]` Implemented and tested for the stated production scope.

Current overall status: **not production-ready**. Most production gates are `[ ]`; current code primarily supports synthetic experiments.

## Gate 0 — Scope, governance, and responsible use

- [~] README clearly states the current prototype is not a validated recession predictor, policy tool, or individual diagnostic.
- [ ] Written product/research scope identifies intended users, allowed uses, prohibited uses, geographies, frequency, and alert recipients.
- [ ] Responsible-use policy blocks individual-level inference, protected-class targeting, unsupported causal claims, and unsupported recession-prediction claims.
- [ ] Human approval workflow exists for model promotion, keyword promotion, threshold changes, and external reports.
- [ ] Legal/terms review is complete for every public data source and LLM provider.
- [ ] Risk register exists for false alarms, missed events, source outages, source drift, public misinterpretation, and model misuse.

## Gate 1 — Real public data ingestion

- [ ] Connector interface exists for public aggregate signal sources.
- [ ] Google Trends connector is implemented with query batching, region/category/time-window controls, rate limiting, retries, and backoff.
- [ ] Google Trends normalization caveats are encoded in documentation and validation checks.
- [ ] At least one additional public signal connector is implemented to reduce single-source dependence.
- [ ] Source registry records owner, endpoint, terms/license, quota, collection cadence, revision behavior, geographic scope, and allowed use.
- [ ] Each ingestion run records query parameters, collection timestamp, source response hash, data vintage, and connector version.
- [ ] Backfill, incremental load, and replay paths are idempotent.
- [ ] Source outage and partial-load behavior is tested.
- [ ] Recorded fixtures exist for connector parsing and schema tests without live network calls.

## Gate 2 — Data storage, lineage, and contracts

- [ ] Immutable raw landing zone stores every source response without destructive overwrite.
- [ ] Curated time-series layer stores validated, normalized aggregate signals.
- [ ] Feature/model-input snapshots are immutable and addressable by ID.
- [ ] Prediction, alert, report, model, and experiment tables or artifact stores exist.
- [ ] Schema contracts validate timestamps, timezones, frequency, required columns, duplicate rows, nulls, ranges, and source metadata.
- [ ] Data quality checks cover freshness, completeness, gaps, unexpected zeroes, source revisions, and distribution shifts.
- [ ] Data retention, archival, and deletion policies are documented.
- [ ] A historical alert can be replayed from stored raw data through report generation.

## Gate 3 — Preprocessing and feature engineering

- [~] Basic winsorization and standardization helpers exist.
- [ ] Train-time transform parameters are persisted and reused at inference time.
- [ ] Feature schema and column ordering are enforced before model inference.
- [ ] Missing-data policy exists per source and feature family.
- [ ] Publication-lag, timezone, frequency alignment, calendar/holiday, and revision semantics are handled.
- [ ] Outliers are tagged with provenance rather than silently clipped only.
- [ ] Leakage tests prove future observations are not used in historical transforms or validation.
- [ ] Feature documentation links every feature to source, ontology node, transform version, and validation status.

## Gate 4 — Ontology and LLM keyword workflow

- [~] Static synthetic ontology/codebook exists.
- [ ] Versioned ontology store exists with concepts, hypotheses, inclusion/exclusion rules, language/geography scope, owner, and review status.
- [ ] LLM prompt templates are versioned and produce structured keyword candidates with rationales.
- [ ] LLM model version, prompt version, parameters, and output are logged for every keyword proposal.
- [ ] Sensitive-term and misuse filters block unsafe terms before review.
- [ ] Human review queue approves/rejects candidate keywords before ingestion.
- [ ] Keyword validation tests stability, redundancy, source availability, drift, event association, and multiple-testing risk.
- [ ] Keyword retirement process preserves history and never silently deletes past features.

## Gate 5 — Modeling and model registry

- [~] Adaptive diagonal Gaussian HMM implementation exists for prototype experiments.
- [ ] Model artifacts include feature schema, transform ID, training dataset ID, config hash, git commit, dependency lock, random seed, and validation report.
- [ ] Model registry supports candidate/staging/production or equivalent states with approvals and rollback.
- [ ] State-label mapping is stable and documented across retraining runs.
- [ ] Model diagnostics cover convergence, non-finite values, likelihood trends, posterior entropy, state occupancy, transition stability, and sensitivity to training windows.
- [ ] Baseline model suite exists for real-world comparisons.
- [ ] Calibration procedure maps posterior scores to alert operating points.
- [ ] Online update or adaptive transition behavior is replayable and auditable.

## Gate 6 — Validation and statistical evidence

- [~] Synthetic validation metrics exist.
- [~] Rolling-origin split helper exists.
- [ ] Real-world event/target catalog is versioned with label definitions, event dates, uncertainty, embargo rules, and owners.
- [ ] Decision-time backtesting uses only data available as of each simulated prediction date.
- [ ] Validation reports include AUC/ranking, Brier score, log predictive density, calibration curves, lead-time distribution, false-alarm rate, precision/recall at operating thresholds, and uncertainty intervals.
- [ ] Robustness checks cover geography, keyword family, source family, frequency, time period, source outages, source revisions, and missing data.
- [ ] Placebo tests, negative controls, and permutation tests are implemented.
- [ ] Multiple-testing correction or hierarchical validation is used for signal discovery.
- [ ] No model can generate reviewed alerts without passing a documented statistical review gate.

## Gate 7 — Continuous orchestration

- [ ] Production scheduler/DAG platform is selected and configured.
- [ ] Ingestion, quality checks, feature generation, training, inference, validation, report generation, and alerting are separate idempotent jobs.
- [ ] Backfill/replay DAGs are separated from live DAGs.
- [ ] Jobs have retries, timeouts, concurrency limits, dependency checks, and failure isolation.
- [ ] Run IDs propagate through every job and artifact.
- [ ] Failed data quality gates block or annotate downstream inference.
- [ ] Operational runbooks cover failed jobs, stale data, source outages, model collapse, bad alerts, and rollback.

## Gate 8 — Alerts and reports

- [ ] Alert rules are tied to calibrated posterior probabilities, persistence requirements, uncertainty, and data quality status.
- [ ] Alert severity levels and recipient routing are documented.
- [ ] Alert suppression, deduplication, acknowledgement, and escalation are implemented.
- [ ] Human-in-the-loop review is required for external alerts until shadow-mode evidence justifies automation.
- [ ] Reports include data sources, data quality status, model version, feature snapshot ID, uncertainty, primary signal contributors, drift status, limitations, and responsible-use language.
- [ ] Alert audit log records score, threshold, model ID, dataset ID, reviewer, delivery status, and postmortem outcome.
- [ ] False-positive and missed-event review processes feed back into validation and threshold governance.

## Gate 9 — Observability

- [ ] Structured logs include run_id, source_id, dataset_id, feature_snapshot_id, model_id, prediction_id, alert_id, and severity.
- [ ] Metrics exist for ingestion freshness, completeness, schema failures, source revisions, job duration, job failures, feature drift, posterior entropy, state occupancy, transition shifts, alert counts, and report delivery.
- [ ] Dashboards show pipeline health, source health, model health, drift, and alert lifecycle.
- [ ] Observability alerts notify maintainers about stale sources, failed DAGs, failed quality checks, model numerical failures, and report-delivery failures.
- [ ] Incident postmortems are stored and linked to affected runs, alerts, reports, and code/model versions.

## Gate 10 — Security and compliance

- [ ] Secrets manager is used for API keys, LLM credentials, and delivery-channel credentials.
- [ ] No secrets are stored in configs, notebooks, logs, Docker images, or committed files.
- [ ] Access control protects dashboards, artifacts, reports, and admin actions.
- [ ] Dependency vulnerability scanning, lockfile review, SBOM generation, and container scanning are in CI/CD.
- [ ] Network egress is controlled for public-source and LLM calls.
- [ ] Audit logs record keyword approvals, source changes, model promotions, threshold changes, alert reviews, and report publication.
- [ ] Data and report retention policies are enforced.

## Gate 11 — Deployment and reliability

- [~] Docker/Docker Compose demo scaffolding exists.
- [ ] Production deployment target is defined.
- [ ] Infrastructure as Code provisions compute, storage, scheduler, secrets, monitoring, and network policy.
- [ ] Environment-specific configs exist for development, staging, and production.
- [ ] Health checks and readiness checks exist for services/jobs.
- [ ] Release process includes versioning, changelog, migration plan, smoke tests, and rollback.
- [ ] Backup and restore procedures are tested.
- [ ] Load tests cover expected keyword/source volume and reporting cadence.
- [ ] Cost monitoring exists for public APIs, LLM usage, storage, and compute.

## Gate 12 — Testing and CI/CD

- [~] Unit tests and GitHub Actions pytest workflow exist for prototype code.
- [ ] CI runs linting, type checks, unit tests, integration tests, contract tests, notebook execution or notebook smoke tests, dependency scan, and container scan.
- [ ] Connector tests use recorded fixtures and cover malformed, partial, stale, and revised responses.
- [ ] Data quality tests cover nulls, duplicates, gaps, outliers, schema drift, and source revisions.
- [ ] Model tests cover numerical stability, deterministic replay, state-label mapping, calibration, and drift monitors.
- [ ] Alert tests cover threshold boundaries, persistence, suppression, escalation, audit logging, and data-quality blocking.
- [ ] Backtest regression tests prevent accidental leakage or metric inflation.
- [ ] Performance tests cover expected historical backfills and live cadence.

## Launch decision rule

The platform should remain **internal research/shadow mode** until Gates 1 through 9 are complete for at least one target geography and signal set, and Gates 10 through 12 have production-equivalent controls. External-facing reports or alerts should require explicit human review until there is a documented operating history with acceptable false-alarm, missed-event, freshness, and drift performance.
