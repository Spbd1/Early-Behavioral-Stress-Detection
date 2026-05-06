# Architecture Gaps Audit

This audit treats the repository as a research prototype that must eventually become a continuously running, reproducible, production-grade experimental platform for early behavioral stress regime detection from real public signals. It is intentionally conservative: if behavior is not implemented in code, tests, configuration, or operational docs, it is marked as missing or placeholder.

## Executive assessment

The repository is a well-labeled synthetic research prototype, not an experimental production platform. The strongest implemented pieces are a synthetic data workflow, a diagonal Gaussian adaptive HMM implementation, synthetic validation metrics, cautious responsible-use messaging, a Streamlit dashboard scaffold, Docker scaffolding, Langflow wrappers, and a small pytest/CI setup. The major production blockers are the absence of real data ingestion, data contracts, scheduler/orchestration, persistence, model registry, online inference service, alerting, report generation, observability, statistical governance for real-world validation, ontology/LLM keyword generation, security controls, and reproducible experiment tracking.

The immediate transformation path should not be to add alerts first. Alerts without source-quality checks, drift monitoring, calibration, backtesting, and human-review policy would create high false-positive and false-negative risk. The platform needs a data integrity and validation spine before any live signal can be trusted.

## Repository inventory and status

| Area | Evidence in repository | Status | Production interpretation |
|---|---|---:|---|
| Package metadata | `pyproject.toml`, `requirements.txt` | Partially implemented | Installable package, but dependency strategy is loose and includes local stub packages that can mask real dependency behavior. |
| Synthetic data | `src/behavioral_stress/data/synthetic.py`, configs, workflow | Implemented for prototype | Useful for method development, not evidence of live performance. |
| Real data ingestion | `src/behavioral_stress/data/ingestion.py` only loads local processed CSVs | Completely missing | No Google Trends/public signal connectors, source provenance, rate limiting, retries, backfills, or licensing controls. |
| Preprocessing | Winsorization and z-score standardization | Partially implemented | No train/serve transform isolation, missingness policy, schema validation, versioned feature transforms, or leakage controls. |
| Adaptive HMM | `src/behavioral_stress/models/adaptive_hmm.py` | Partially implemented | Core algorithm exists, but lacks model artifact management, calibration, online serving contract, uncertainty governance, and production numerical monitoring. |
| Baselines | Logistic baseline plus neural placeholders | Placeholder/partial | Not enough comparative models for model risk management. |
| Conditional/covariate modeling | Lightweight conditional HMM | Partial/prototype | No real exogenous covariate ingestion or validation. |
| Ontology/codebook | Static synthetic ontology/codebook | Placeholder/partial | No governed ontology lifecycle, keyword generation workflow, review queue, versioning, or LLM traceability. |
| Signal discovery | Feature screening, dimensionality helper, retirement flags | Partial/prototype | No automated discovery from public data, no multiple-testing controls, no stability gates, no review workflow. |
| Validation | Synthetic metrics and rolling-origin split helper | Partial/prototype | Lacks real-world temporal validation, event labels, calibration curves, confidence intervals, placebo tests, and pre-registered evaluation plans. |
| Causal diagnostics | Event-study template, negative control diagnostic, sensitivity placeholder | Placeholder | Correctly cautious, but insufficient for any causal claim or policy interpretation. |
| Dashboard | Streamlit local output viewer | Placeholder/demo | Not an operational monitoring console. No auth, live status, incident context, alert audit trail, or data quality views. |
| Langflow | JSON scaffold and wrapper components | Placeholder/demo | Good prototyping surface, not a production workflow engine. |
| Reports/alerts | Report wrapper metadata only | Completely missing | No alert rules, suppression, escalation, SLOs, human approval, templated reports, or distribution channels. |
| Orchestration | CLI scripts only | Completely missing | No scheduler, queues, idempotent jobs, state recovery, or backfill orchestration. |
| Storage | CSV files under `data/` | Placeholder/demo | No durable raw/bronze/silver/gold layers, database, object store, data catalog, lineage, or retention policy. |
| Observability | Minimal logging helper and CI output | Completely missing | No metrics, traces, structured logs, data quality dashboards, alerting on pipeline/model health. |
| Security | `.env.example`, Docker scaffold | Mostly missing | No secrets manager, access control, dependency scanning, SBOM, signing, or network policy. |
| Testing | Pytest for core prototype behavior | Partial | No integration tests against real connectors, contract tests, property tests, load tests, replay tests, or alert tests. |
| Deployment | Dockerfile/compose and GitHub Actions tests | Placeholder/partial | No production environment manifests, IaC, release process, rollbacks, health checks, or runbooks. |

## Already implemented

- Synthetic aggregate regime generator with latent states, codebook generation, covariates, metadata, and warnings.
- Diagonal Gaussian adaptive HMM with fit, forward/backward, smoothing, Viterbi path, and JSON persistence utilities.
- Lightweight preprocessing helpers for winsorization and standardization.
- Synthetic validation metrics such as ROC-AUC-like ranking, Brier score, log predictive density, and simple lead time.
- Rolling-origin split utility with no future leakage in slice construction.
- Basic signal screening, retirement diagnostics, and dimensionality helper.
- Static ontology/codebook objects for aggregate synthetic signals.
- Streamlit dashboard that reads local synthetic workflow outputs.
- Langflow scaffold and Python fallback workflow.
- Docker and Docker Compose scaffolding for demo, dashboard, and optional Langflow.
- GitHub Actions CI for install, compile, and pytest across Python 3.10/3.11.

## Partially implemented but not production-ready

### Modeling core

The HMM implementation is meaningful for prototype experiments, but a production experimental platform also needs:

- fit/predict API contracts that persist transform parameters and feature schemas with each model artifact;
- explicit model versioning and immutable artifacts;
- model registry metadata for training data snapshot, code version, config hash, random seed, and validation report;
- calibration and threshold selection procedures tied to operating points;
- monitoring for non-finite likelihoods, posterior collapse, state-label switching, unstable transition matrices, and sensitivity to retraining windows;
- online update semantics that are auditable and replayable.

Why it matters: latent regime models can appear stable on synthetic data while silently drifting, relabeling states, or overreacting to source artifacts in live data. Without artifact lineage and diagnostics, alerts become hard to trust or debug.

### Preprocessing

Current preprocessing is column-wise clipping and standardization. It does not yet distinguish training-time and serving-time transforms.

Missing safeguards include:

- train-only quantile/mean/std fitting with frozen transform artifacts;
- missing data policies by signal/source;
- outlier provenance tagging rather than only clipping;
- feature schema enforcement and column ordering guarantees;
- unit normalization, frequency alignment, timezone handling, holiday effects, and publication-lag handling;
- leakage tests to ensure future data is never used in historical inference.

Why it matters: public time series often revise, shift frequency, omit regions, or change semantics. Feature leakage and inconsistent transforms can produce exaggerated early-warning performance.

### Validation

Synthetic validation exists, but real-world validation is mostly absent. Required additions include:

- labeled event catalog with versioned event definitions and embargo periods;
- rolling-origin backtests using only data available at each decision time;
- calibration curves, reliability diagrams, threshold/lead-time tradeoff curves, confidence intervals, and false-alarm accounting;
- negative controls, placebo windows, permutation tests, multiple-hypothesis correction for keyword/signal discovery;
- robustness checks across geographies, frequency, keyword families, vintages, and source outages;
- comparison against naive baselines and public benchmark indicators.

Why it matters: the goal is early detection, so false optimism from lookahead, survivorship, or cherry-picked events is the central scientific risk.

## Placeholder/demo-only components

- `src/behavioral_stress/data/ingestion.py` explicitly states real connectors are not implemented and only loads processed CSVs.
- Langflow files are wiring scaffolds around the synthetic workflow, not a maintained production orchestration layer.
- Streamlit dashboard reads local synthetic CSV outputs and includes drift diagnostic placeholders.
- Docker Compose services run demos, not long-lived production jobs.
- Neural baselines raise `NotImplementedError`.
- Causal sensitivity is a placeholder returning a status dictionary.
- Local stub modules under `src/sklearn`, `src/scipy`, `src/statsmodels`, `src/plotly`, `src/streamlit.py`, and `src/yaml.py` appear to exist to keep lightweight tests runnable when external packages are absent. These are useful for constrained demos but risky in production because they can shadow real libraries and hide integration failures.

## Completely missing production subsystems

### 1. Real public-signal ingestion

Required scope:

- Google Trends connector with source-specific semantics, API/library constraints, quotas, retry/backoff, rate limiting, regional controls, keyword batch normalization behavior, and reproducible historical snapshots.
- Additional public signals connector framework, such as macro indicators, mobility/public attention signals, job-market series, web/search trend alternatives, news volume, or other permitted aggregate sources.
- Ingestion manifests capturing source URL/API, query parameters, region, category, collection timestamp, license/terms notes, response hash, and data vintage.
- Backfill, incremental load, replay, and source outage handling.

Why it matters: Google Trends values are normalized and can change depending on query batches, time range, region, and sampling. Without source-aware ingestion and provenance, downstream regime changes can be data artifacts.

### 2. Data lake/warehouse and contracts

Required scope:

- Raw immutable landing zone, cleaned time-series tables, feature store or equivalent, model input snapshots, prediction tables, alert tables, and report archive.
- Schema contracts using tools such as Pydantic/Pandera/Great Expectations or equivalent.
- Data quality checks for freshness, completeness, duplicate timestamps, frequency gaps, value ranges, unexpected zeroes, source revisions, and distribution shifts.
- Dataset versioning and retention policy.

Why it matters: experimental production requires replayability. If the platform cannot reconstruct the exact input snapshot that produced an alert, it cannot be audited or scientifically improved.

### 3. Ontology-guided LLM keyword workflow

Required scope:

- Ontology version store with concepts, signal hypotheses, inclusion/exclusion criteria, geography/language scope, and owner/reviewer metadata.
- Lightweight LLM prompt templates for keyword proposal, expansion, contradiction checks, and summarization.
- Human-in-the-loop review and approval before any keyword enters live collection.
- Safety filters for sensitive, individual-level, medical, or protected-class terms.
- Keyword experiment metadata linking generated terms to ontology node, prompt version, model version, reviewer, and validation status.

Why it matters: generated keywords can encode bias, leak sensitive concepts, or overfit known events. Governance is needed before public behavioral traces are used for alerts.

### 4. Continuous orchestration

Required scope:

- Scheduler such as Airflow, Dagster, Prefect, Argo, or a managed equivalent.
- Idempotent ingestion, transformation, training, inference, validation, reporting, and alerting jobs.
- Backfill and replay DAGs separated from live DAGs.
- Job-level retries, timeouts, dead-letter handling, concurrency controls, and dependency-aware recovery.

Why it matters: continuous systems fail in mundane ways: partial loads, duplicate runs, delayed sources, and retry storms. The prototype has no run state model for these failures.

### 5. Alerting and report reliability

Required scope:

- Alert definitions tied to calibrated posterior probabilities, persistence rules, lead-time targets, and uncertainty bands.
- Suppression/deduplication rules, severity taxonomy, recipient routing, acknowledgement workflow, and incident log.
- Human-review gate for external-facing alerts until the system has a validated track record.
- Report generation templates that include caveats, data quality status, model version, signal contributors, drift state, and uncertainty.

Why it matters: a noisy stress alert can cause reputational damage and operational fatigue. Reliability depends as much on alert policy as model score.

### 6. Observability

Required scope:

- Structured application logs with run IDs, dataset IDs, model IDs, and alert IDs.
- Metrics for ingestion freshness, completeness, schema violations, transform drift, model score distribution, posterior entropy, alert counts, false-alarm review outcomes, and runtime errors.
- Distributed tracing or run lineage across DAG steps.
- Dashboards and alerts for pipeline health, data quality, model drift, and report delivery.

Why it matters: production failures are often silent in data products. A regime alert is meaningless if the input pipeline was stale or a source changed its sampling method.

### 7. Security, privacy, and compliance controls

Required scope:

- Secrets manager integration and no secrets in configs or notebooks.
- Network egress controls for public API calls.
- Dependency vulnerability scanning, lockfiles, SBOM, image scanning, and signed releases.
- Access control for dashboards, model artifacts, alerts, and reports.
- Responsible-use policy preventing individual-level inference and sensitive targeting.

Why it matters: even aggregate public signals can create policy, reputational, and misuse risk. The system must make inappropriate uses difficult by design.

### 8. Deployment and operations

Required scope:

- Production container image with pinned dependencies and no local stub modules shadowing real packages.
- Environment-specific configuration for dev/staging/prod.
- Infrastructure as Code, health checks, readiness checks, graceful shutdown, log routing, backup/restore, runbooks, and rollback process.
- Model and data migration process.

Why it matters: Docker Compose demos are not deployment architecture. Continuous inference requires reliable state, monitoring, secrets, and release controls.

## Broken or risky components

| Component | Risk | Why it matters | Recommended action |
|---|---:|---|---|
| Local stubs for major libraries | High | `src/sklearn`, `src/scipy`, `src/statsmodels`, `src/plotly`, `src/streamlit.py`, and `src/yaml.py` can shadow real packages and make CI pass with fake behavior. | Move stubs to tests-only fixtures or remove once dependencies are installed in CI. Add an import-origin check. |
| Real ingestion module | Critical | It explicitly does not implement connectors, yet production goal depends on Google Trends/public signals. | Build connector interfaces and provenance first. |
| CSV-only persistence | High | Local CSVs do not provide transactional safety, lineage, schema evolution, or concurrent access. | Add object-store/database-backed raw and curated layers. |
| Dashboard | Medium | It may look operational but only renders synthetic local files. | Rename or label as demo until connected to monitored production tables. |
| Validation metrics | High | Synthetic labels are known; real labels and decision-time availability are missing. | Build real backtesting harness before live alerts. |
| Alert/report layer | Critical | No actual alert generation exists. | Implement only after data quality, calibration, and review gates. |
| Dependency pinning | Medium | Unpinned broad dependencies can change behavior. | Add lockfile and image reproducibility process. |
| Notebooks | Medium | Notebooks can drift from package code and may not run in CI. | Add notebook execution checks or convert critical notebooks to scripts/tests. |

## Architectural weaknesses

1. **Synthetic-first architecture has no transition seam to real data.** The workflow calls the synthetic generator directly and writes fixed local CSVs. A production system needs source-agnostic dataset interfaces, source-specific connectors, and data contracts.
2. **No immutable lineage.** The system writes outputs but does not create content-addressed dataset/model artifacts or link predictions to exact inputs.
3. **No decision-time semantics.** Early warning depends on what was known at a date. Current validation can use generated truth and current files without vintage/availability constraints.
4. **No governed state interpretation.** HMM state numbers can switch across training runs. Production reports need stable regime labeling, state-mapping rules, and uncertainty language.
5. **No alert operating policy.** A posterior probability is not an alert. Alerts require calibration, thresholds, persistence, review, and escalation rules.
6. **No source reliability model.** Public signals can be delayed, resampled, revised, or rate-limited. The architecture must treat source behavior as first-class.
7. **No LLM governance.** Ontology generation is absent, and any future keyword proposal workflow must be versioned and reviewed.
8. **No production observability.** There is no way to distinguish a true regime shift from stale data, source drift, failed jobs, or model collapse.

## Statistical validation gaps

- No real event label catalog or documented target definition.
- No benchmark comparison to simple rules, lagged macro indicators, static HMMs, change-point models, or no-skill baselines in real data.
- No prequential/online evaluation where each prediction uses only prior vintages.
- No uncertainty intervals around lead time, AUC, Brier score, false-alarm rate, or alert precision.
- No multiple-testing correction for signal discovery and keyword expansion.
- No geography/time/frequency stratification analysis.
- No calibration governance or threshold selection protocol.
- No analysis of state identifiability, label switching, posterior entropy, or state persistence stability.
- No simulated source outages, data revisions, or adversarial drift tests.
- No independent holdout period or frozen challenge set.

## Observability gaps

- Missing run IDs propagated through ingestion, transforms, modeling, reports, and alerts.
- Missing data freshness metrics and source health checks.
- Missing feature drift and concept drift monitors.
- Missing model health monitors: likelihood trends, posterior entropy, transition matrix shifts, state occupancy, failed convergence, non-finite values.
- Missing alert quality monitors: alert volume, deduplication, acknowledgements, false-positive review, missed-event postmortems.
- Missing dashboard for lineage and run status.
- Missing audit log for keyword additions, model promotions, threshold changes, and report publication.

## Reproducibility gaps

- No lockfile for Python dependencies.
- No dataset versioning or immutable raw snapshots.
- No model registry or experiment tracker.
- No config hashing, code commit stamping, environment capture, or artifact manifests for every run.
- No notebook execution in CI.
- No random-seed strategy across all stochastic steps beyond synthetic/HMM paths.
- No official way to replay a historical alert end-to-end.

## Security and reliability risks

- Public API credentials and LLM credentials will need secret storage; no integration exists.
- No dependency vulnerability scanning or image scanning.
- Local stub packages can hide real dependency vulnerabilities and runtime incompatibilities.
- No authn/authz for dashboards or reports.
- No backup/restore or disaster-recovery plan.
- No rate-limit protection for public data sources.
- No data retention and deletion policy.
- No misuse-prevention policy beyond README warnings.

## Deployment gaps

- Docker Compose is demo-only and profile-based, not production deployment.
- No Kubernetes/ECS/Batch/Cloud Run/VM deployment target is defined.
- No IaC, environment promotion, release versioning, rollback, health checks, or runbooks.
- No persistent volume/database/service definitions for production data.
- No job scheduler deployment.
- No alert delivery infrastructure.

## Testing gaps

- No connector unit tests because connectors do not exist.
- No contract tests for source schemas and source semantics.
- No integration tests with recorded Google Trends/public-source fixtures.
- No property-based tests for HMM numerical stability and preprocessing invariants.
- No backtest regression tests for historical windows.
- No drift detector tests.
- No alert rule tests for persistence, suppression, severity, and audit logging.
- No security tests, dependency scan, or container scan in CI.
- No load/performance tests for larger keyword panels.
- No chaos tests for delayed/missing/revised source data.

## Dependency graph of missing systems

```text
Governance and responsible-use policy
  ├─ Ontology scope and review policy
  │   └─ LLM keyword generation workflow
  │       └─ Approved keyword registry
  │           └─ Public-signal ingestion manifests
  ├─ Validation target/event definitions
  │   └─ Backtesting harness
  │       └─ Calibration and threshold policy
  │           └─ Alert/reports policy
  └─ Security/compliance controls
      └─ Production deployment controls

Source connector framework
  ├─ Google Trends connector
  ├─ Other public-source connectors
  ├─ Rate limiting/retries/backfills
  └─ Raw immutable data store
      └─ Data contracts and quality checks
          └─ Feature pipeline and transform registry
              ├─ Model training pipeline
              │   └─ Model registry and validation reports
              └─ Online/batch inference pipeline
                  └─ Prediction store
                      └─ Alert engine
                          └─ Report generator and delivery

Orchestration platform
  ├─ Scheduled ingestion jobs
  ├─ Scheduled validation/retraining jobs
  ├─ Scheduled inference/report jobs
  └─ Observability and incident response
```

## Prioritized roadmap summary

1. Establish governance, source contracts, and data integrity foundation.
2. Build real-source ingestion and immutable storage before modeling live data.
3. Add reproducible feature pipelines and experiment tracking.
4. Build rigorous real-world backtesting and calibration.
5. Introduce ontology-guided LLM keyword generation with human review.
6. Productionize model artifacts, online/batch inference, and drift monitoring.
7. Implement reports and alerts with conservative human-in-the-loop safeguards.
8. Add deployment, security, observability, and operational runbooks.

See `ROADMAP.md` for phases, difficulty, risk, dependencies, and acceptance criteria. See `FINALIZATION_CHECKLIST.md` for a gate-by-gate launch checklist.
