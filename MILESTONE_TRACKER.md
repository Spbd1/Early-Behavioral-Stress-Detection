# Milestone Tracker

This tracker is initialized from `IMPLEMENTATION_PLAN.md`, `FINALIZATION_CHECKLIST.md`, and `ROADMAP.md`. It should be updated at the end of every implementation milestone. Status values are `Not started`, `In progress`, `Blocked`, `Validation pending`, `Complete`, or `Deferred`.

## Must-have production requirements

| ID | Milestone | Status | Blockers | Dependencies | Validation state | Technical debt notes |
|---|---|---|---|---|---|---|
| P0 | Governance, scope, and prototype boundary freeze | Not started | Stakeholder agreement needed for intended users, geographies, cadence, alert recipients, and prohibited uses. | None | Not validated; documentation and repository-claim review pending. | README warnings are partial; prototype/stub inventory needs an owner and update process. |
| P1 | Source registry, contracts, and local storage foundation | Validation pending | Storage backend remains local filesystem; legal/terms review still required before scheduled live collection. | P0 | Partially validated by `tests/test_google_trends_ingestion.py`; local raw/processed/metadata separation and cache replay tests added. | Local CSV/JSON storage is sufficient for research replay but not an append-only production lake or governed source registry. |
| P2 | Connector interface and Google Trends ingestion | Validation pending | Legal/terms review for source collection; pytrends remains an unofficial connector and should be replaceable if reliability requirements increase. | P0, P1 | Fixture-based tests added for retry/backoff, batching, cache replay, raw/processed separation, metadata, validation, and anchor normalization. Live-network tests intentionally excluded. | Connector abstraction, config, CLI, and filesystem cache now exist; remaining debt is provider volatility, source governance, and production storage hardening. |
| P3 | Curated features, transform registry, and feature snapshots | Not started | Feature schema conventions, missing-data policy, and transform metadata format pending. | P1, P2 | Not validated; transform persistence, leakage, schema-ordering, and snapshot immutability tests pending. | Current winsorization/standardization helpers are not sufficient for inference-time reuse. |
| P4 | Experiment tracking and model registry foundation | Not started | Registry backend and approval metadata format pending; dependency lock strategy pending. | P3 | Not validated; artifact metadata, diagnostics, registry transition, and rollback tests pending. | Current adaptive HMM is prototype-ready but lacks production artifact metadata and lifecycle states. |
| P5 | Decision-time validation, baselines, and calibration governance | Not started | Event/target catalog definitions, label vintages, and review ownership pending. | P3, P4 | Not validated; decision-time backtest, baseline, calibration, robustness, and statistical review tests pending. | Synthetic validation exists, but real-world evidence and calibration governance are missing. |
| P6 | Shadow-mode inference and drift monitoring | Not started | Scheduler choice, prediction store shape, monitoring thresholds, and internal report format pending. | P4, P5 | Not validated; idempotent inference, data-quality blocking, drift monitor, logging, dashboard, and runbook tests pending. | Drift monitoring is placeholder-only and operational observability is missing. |
| P7 | Human-reviewed experimental alert workflow | Not started | Reviewer workflow owner, delivery policy, alert severity taxonomy, and postmortem process pending. | P5, P6 | Not validated; alert rule, suppression, approval gate, audit field, and blocked-delivery tests pending. | Alerting must remain disabled until calibrated thresholds and statistical review are approved. |
| P8 | Security, deployment, and operational hardening | Not started | Deployment target, secrets provider, auth model, IaC platform, and SLO ownership pending. | P1-P7 for full production hardening; CI improvements can begin earlier after P0. | Not validated; CI, scan, access-control, backup/restore, rollback, and load tests pending. | CI/CD is partial; secrets, auth, IaC, backup/restore, and performance evidence are missing. |

## Research enhancements

| ID | Milestone | Status | Blockers | Dependencies | Validation state | Technical debt notes |
|---|---|---|---|---|---|---|
| R1 | Governed ontology and LLM keyword workflow | Validation pending | LLM provider terms review, sensitive-term policy, reviewer staffing, and production prompt governance remain pending. | P0; ingestion promotion also requires P2-P3. | Partially validated by `tests/test_keyword_generation.py`; local ontology categories, deterministic RAG grounding, geo-aware schema, review gates, deduplication, expansion limits, versioning, retirement, unsupported-location handling, and drift-review heuristics added. | Current workflow is deterministic/local and does not call an LLM; future LLM use must persist prompts, model versions, raw outputs, and reviewer decisions before promotion. |
| R2 | Multi-source and multi-region research panels | Not started | Additional source selection, terms review, region scope, and cost expectations pending. | P1-P3; comparative validation requires P5. | Not validated; additional connector fixture tests and multi-region snapshot validation pending. | Single-source dependence remains a critical risk until another aggregate source is integrated. |
| R3 | Robustness, placebo, and negative-control evidence pack | Not started | Approved event catalog, feature snapshots, and statistical review rubric pending. | P5 | Not validated; robustness report, placebo, negative-control, source-outage, and sensitivity tests pending. | Causal/validation modules exist but need registry-backed evidence packaging and caveat discipline. |
| R4 | Advanced model comparison automation | Not started | Comparable model configurations, compute budget, and model promotion criteria pending. | P4, P5 | Not validated; model comparison runner and metric-parity tests pending. | Baseline coverage is partial and comparisons are not yet registry-backed. |

## Optional experimental features

| ID | Milestone | Status | Blockers | Dependencies | Validation state | Technical debt notes |
|---|---|---|---|---|---|---|
| X1 | Interactive research dashboard extensions | Deferred | Must not distract from storage, validation, and alert governance; access-control design pending for broad use. | P6 for artifact-backed display; P8 for non-local deployment. | Not validated; read-only dashboard and artifact-citation smoke tests pending. | Dashboard/demo scaffolds should not become de facto production orchestration. |
| X2 | Cost and performance simulation harness | Deferred | Planned source/keyword/region volumes and provider cost assumptions pending. | P2-P3 for realistic parameters; P8 for load-test integration. | Not validated; deterministic simulator and load-test threshold tests pending. | No cost monitoring or capacity model exists. |
| X3 | Automated periodic independent review package | Deferred | Reviewer process, access controls, and evidence-bundle scope pending. | P5; stronger value after P7 alert audit data; P8 for secure sharing. | Not validated; manifest generation and reproduction-instruction tests pending. | Independent review should not be represented as complete until human sign-off exists. |

## Cross-milestone validation ledger

| Validation area | Current state | Next milestone to advance | Notes |
|---|---|---|---|
| Repository claim/safety scan | Pending | P0 | Confirm docs and demos do not imply validated production, diagnostic, causal, or recession-prediction capability. |
| Source terms and registry review | In progress | P1 | Local source metadata exists, but legal/terms and production registry review remain required before scheduled live connector operation. |
| Fixture-only connector tests | Added | P2 | `tests/test_google_trends_ingestion.py` covers retries, batching, cache replay, validation, normalization, and artifact separation without live Google calls. |
| Immutable raw-to-feature replay | Partial | P3 | Raw, processed, cache, and metadata artifacts are separated for Google Trends, but immutable snapshot manifests are still pending. |
| Model artifact reproducibility | Pending | P4 | Must include git commit, dependency lock, config hash, feature snapshot, and seed. |
| Decision-time backtesting | Pending | P5 | Must prove no future information is used. |
| Calibration and threshold approval | Pending | P5 | Required before any alert milestone can proceed. |
| Shadow-mode operational health | Pending | P6 | Must run internally with no external delivery. |
| Human-reviewed alert auditability | Partial for keyword governance only | R1/P7 | Keyword candidates now have human review states and version history; alert auditability remains pending and RAG is explicitly excluded from alert decisions. |
| Deployment and rollback evidence | Pending | P8 | Required for controlled production operation. |

## Update protocol

When a milestone implementation begins or completes:

1. Update the milestone row status, blockers, dependencies, validation state, and technical debt notes.
2. Link or name the validation artifacts produced by the milestone.
3. Record any new risks in `docs/risk_register.md` once that file exists.
4. Update `FINALIZATION_CHECKLIST.md` gate statuses only when code, configuration, tests, documentation, and operational evidence exist.
5. Keep deferred optional work deferred unless it has no negative impact on must-have production requirements.
