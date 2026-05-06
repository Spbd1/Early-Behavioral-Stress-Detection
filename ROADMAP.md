# Roadmap to an Experimental Production Platform

This roadmap assumes the target is a continuously running experimental system that ingests real public aggregate signals, detects early behavioral stress regimes using adaptive HMMs and related methods, and produces cautious reports/alerts. It deliberately sequences data integrity and validation before alerting.

## Difficulty and risk scale

- Difficulty: **S** small, **M** moderate, **L** large, **XL** multi-team or high-complexity.
- Risk: **Low**, **Medium**, **High**, **Critical** based on probability and impact of misleading alerts, unreproducible science, operational failure, or misuse.

## Phase 0 — Freeze prototype boundaries and remove ambiguity

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Declare synthetic-only scope in all demos | Partially implemented | S | Medium | None | Every demo/dashboard/report clearly says synthetic-only until real-data gates pass. |
| Inventory placeholders and stubs | Partially implemented | S | High | None | A maintained inventory exists for demo-only modules, stubs, and NotImplemented paths. |
| Define target operating mode | Missing | M | High | Stakeholder input | Written product/research spec states users, alert recipients, prohibited uses, target geographies, and decision cadence. |
| Define responsible-use policy | Partial README warnings | M | Critical | Operating mode | Policy forbids individual inference, protected-class targeting, causal/policy claims without separate evidence, and unsupported recession-prediction claims. |

## Phase 1 — Data governance, contracts, and storage foundation

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Source registry | Missing | M | Critical | Phase 0 policy | Registry records source owner, endpoint, license/terms, quota, geography, frequency, revision behavior, and allowed use. |
| Dataset schema contracts | Missing | M | Critical | Source registry | Contracts validate timestamps, frequency, required fields, ranges, nulls, duplicates, and source metadata. |
| Immutable raw storage | Missing | L | Critical | Source registry | Every source response lands in append-only raw storage with hash, collection timestamp, query parameters, and data vintage. |
| Curated time-series store | Missing | L | High | Raw storage, contracts | Cleaned features are stored in versioned tables/files with lineage back to raw source snapshots. |
| Data quality checks | Missing | M | Critical | Contracts | Freshness, completeness, gaps, revisions, outliers, and distribution changes produce machine-readable status. |
| Backfill/replay conventions | Missing | M | High | Raw and curated stores | Historical rebuilds are idempotent and never overwrite raw evidence. |

## Phase 2 — Real public-signal ingestion

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Connector interface | Missing | M | High | Phase 1 contracts | Connectors share a typed interface for fetch, normalize, validate, persist, and replay. |
| Google Trends connector | Missing | L | Critical | Connector interface, source registry | Connector handles query batching, region/category/time windows, normalization caveats, retries, rate limits, and response provenance. |
| Additional public-source connectors | Missing | L | High | Connector interface | At least one non-search signal source is integrated to reduce single-source dependence. |
| Recorded fixtures | Missing | M | High | Connectors | Tests use frozen API responses/fixtures to validate parsing and schema behavior without live network dependence. |
| Source outage handling | Missing | M | High | Orchestration, data quality | Stale, partial, or failed source loads block or annotate downstream inference. |

## Phase 3 — Ontology-guided LLM keyword workflow

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Ontology version store | Static synthetic codebook | M | High | Phase 0 policy | Concepts, hypotheses, exclusions, geography/language scope, and owners are versioned. |
| Keyword proposal prompts | Missing | M | Medium | Ontology store | Prompt templates are versioned, tested, and produce structured candidate terms with rationale. |
| Human review queue | Missing | L | Critical | Keyword prompts, policy | No keyword enters live ingestion without approval and audit metadata. |
| Sensitive-term filters | Missing | M | Critical | Policy | Workflow blocks individual diagnosis, protected-class targeting, and unsafe sensitive terms. |
| Keyword validation harness | Missing | L | High | Real ingestion, backtesting | Candidate terms are tested for stability, redundancy, drift, and event association before promotion. |

## Phase 4 — Reproducible feature and experiment pipeline

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Transform registry | Missing | M | Critical | Curated store | Train-time preprocessing parameters are persisted and reused at inference time. |
| Feature store or model input snapshots | Missing | L | Critical | Transform registry | Every model run references immutable feature snapshots. |
| Experiment tracking | Missing | M | High | Feature snapshots | Runs store config hash, git commit, dependency lock, seed, dataset IDs, metrics, and artifacts. |
| Model registry | Missing | L | High | Experiment tracking | Models have stages, validation reports, promotion approvals, and rollback metadata. |
| Dependency lock and build provenance | Missing | M | Medium | CI/CD | Releases use pinned dependencies and reproducible container builds. |

## Phase 5 — Real-world validation and statistical governance

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Event/target catalog | Missing | L | Critical | Policy | Event definitions, dates, vintages, label uncertainty, embargoes, and owners are versioned. |
| Decision-time backtesting | Missing | XL | Critical | Feature snapshots, event catalog | Backtests only use data available as of each simulated date. |
| Baseline suite | Partial | L | High | Backtesting | Static HMM, naive persistence, change-point, macro lag, and classifier baselines are compared. |
| Calibration and thresholds | Missing | L | Critical | Backtesting | Thresholds are selected with documented false-alarm/lead-time tradeoffs and uncertainty intervals. |
| Robustness and placebo tests | Missing | L | High | Backtesting | Results survive geography, frequency, keyword-family, source-outage, placebo, and negative-control checks. |
| Statistical review gate | Missing | M | Critical | Validation artifacts | Human approval is required before any model/threshold can generate operational alerts. |

## Phase 6 — Production inference, drift monitoring, and alerting

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Batch/online inference job | Missing | L | High | Model registry, orchestration | Inference is idempotent, versioned, replayable, and blocks on failed data quality checks. |
| Drift monitors | Placeholder only | L | Critical | Feature snapshots, predictions | Monitors cover source freshness, feature distribution, posterior entropy, state occupancy, likelihood, and transition stability. |
| Alert engine | Missing | L | Critical | Calibration, drift monitors | Alerts use persistence, uncertainty, suppression, severity, and data-quality annotations. |
| Human-in-the-loop review | Missing | M | Critical | Alert engine | External reports/alerts require review until sufficient validated operating history exists. |
| Report generator | Missing | M | High | Prediction store, alert engine | Reports include model/data versions, caveats, uncertainty, drivers, drift status, and responsible-use text. |
| Alert audit table | Missing | M | High | Alert engine | Every alert has score, threshold, data status, model ID, reviewer, delivery status, and postmortem fields. |

## Phase 7 — Orchestration, observability, and operations

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Production scheduler | Missing | L | Critical | Ingestion and inference jobs | DAGs support retries, timeouts, backfills, dependency checks, and failure isolation. |
| Structured logging | Missing | M | High | Run ID conventions | Logs include run_id, dataset_id, model_id, source_id, alert_id, and severity. |
| Metrics and dashboards | Missing | L | Critical | Data/model/alert metrics | Operators can see data freshness, job health, model health, drift, and alert status. |
| Incident runbooks | Missing | M | High | Observability | Runbooks cover stale sources, failed DAGs, model collapse, false alerts, and rollback. |
| SLOs and on-call policy | Missing | M | Medium | Operational ownership | Freshness, inference, and report delivery SLOs are defined and monitored. |

## Phase 8 — Security, deployment, and scale

| Workstream | Status today | Difficulty | Risk if skipped | Dependencies | Acceptance criteria |
|---|---:|---:|---:|---|---|
| Secrets management | Missing | M | Critical | Deployment target | API keys and LLM credentials never appear in files, logs, notebooks, or images. |
| Access controls | Missing | L | High | Deployment target | Dashboards, artifacts, reports, and admin actions require authentication/authorization. |
| CI/CD hardening | Partial | M | High | Dependency lock | CI includes tests, lint, type checks, dependency scan, container scan, and release artifact generation. |
| Infrastructure as Code | Missing | L | High | Deployment target | Environments are reproducible and reviewed through code. |
| Rollback and backup/restore | Missing | M | High | Storage and deployment | Data, models, and services can be restored or rolled back with tested procedures. |
| Performance/load testing | Missing | M | Medium | Real pipelines | Platform handles planned keyword/source volume with bounded latency and cost. |

## Suggested implementation milestones

### Milestone A — Trusted offline real-data lab

Goal: run repeatable offline experiments on real public aggregate signals without alerts.

Must include:

- source registry;
- Google Trends connector with immutable raw snapshots;
- schema/data-quality checks;
- feature snapshots;
- experiment tracking;
- recorded connector fixtures;
- initial decision-time backtesting harness.

### Milestone B — Governed keyword and validation loop

Goal: safely expand and validate ontology-guided signal panels.

Must include:

- versioned ontology;
- LLM prompt and output schemas;
- human review queue;
- sensitive-term filters;
- keyword validation harness;
- baseline suite;
- calibration reports.

### Milestone C — Shadow-mode continuous operation

Goal: run live ingestion and inference continuously with no external alerts.

Must include:

- scheduler;
- production storage;
- model registry;
- inference job;
- drift monitors;
- internal-only reports;
- operational dashboards;
- runbooks.

### Milestone D — Reviewed experimental alerts

Goal: generate cautious alerts with human approval and full auditability.

Must include:

- calibrated alert rules;
- uncertainty and data-quality gating;
- suppression and acknowledgement;
- reviewer workflow;
- alert audit log;
- false-positive/missed-event review process.

### Milestone E — Scaled experimental platform

Goal: support future scaling across regions, signal families, models, and experiments.

Must include:

- multi-region feature partitions;
- model comparison automation;
- cost monitoring;
- stronger security controls;
- documented release and rollback process;
- periodic independent validation review.

## Critical path

```text
Responsible-use policy
  -> source registry
  -> real ingestion + raw snapshots
  -> data contracts + quality gates
  -> feature snapshots + transform registry
  -> experiment/model registry
  -> decision-time backtesting
  -> calibration/threshold governance
  -> shadow-mode inference + drift monitoring
  -> human-reviewed reports/alerts
```

## Areas that should not be built first

- **Do not build external alerts before data quality and calibration.** This would maximize false-alarm risk.
- **Do not rely on LLM-generated keywords without review.** Keyword drift and sensitive-term risks are high.
- **Do not treat Streamlit/Langflow scaffolds as production orchestration.** They are useful for demos but lack operational guarantees.
- **Do not use synthetic validation metrics as launch evidence.** They are useful for unit testing and method sanity checks only.
