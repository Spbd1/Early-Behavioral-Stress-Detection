# Milestone Tracker

Date: 2026-05-07

## Current overall status

- **Classification:** experimental MVP / research prototype.
- **Production readiness:** not production-ready.
- **Validated path:** synthetic/offline/mock local path.
- **Not validated:** live Google Trends, real browser automation, Docker runtime, production deployment, calibrated thresholds, and prospective real-world performance.
- **Claim guardrail:** not a recession predictor.

## Milestones

| Milestone | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Synthetic workflow | Implemented / locally validated | `run_synthetic_demo.py`, `run_validation.py`, pytest coverage | Broader scientific validation remains required |
| Adaptive HMM MVP | Implemented / locally tested | Unit and workflow tests pass | Calibration and real-world robustness not established |
| Ontology/keyword governance scaffold | Partial MVP | Local registry/RAG tests and docs | Human governance workflows and provider review remain deferred |
| Google Trends ingestion | Offline/mock path validated | Dry-run config, cache, artifacts, and tests pass | Live pytrends/provider validation and legal review not done |
| MVP BSI | Implemented as heuristic MVP | BSI contract tests and dashboard payloads | Full `BSI_DESIGN.md`, calibrated uncertainty, and approved thresholds deferred |
| Geo-aware alerting/reporting | MVP implemented | Geo alerting/report tests pass; JSONL alert history exists | Production DB-backed replay/audit state and human workflow deferred |
| Browser dashboard/static UI | Synthetic/demo-oriented MVP | Dashboard payload build and frontend static tests pass | Real Chrome automation and real-world monitoring validation not done |
| Lint/quality gate | Passing | `ruff check` passes locally | Keep lint passing in future changes |
| Docker/deployment | Scaffold only | Docker files/docs exist | Runtime validation not run in this final local pass |

## Historical notes now resolved

- Earlier notes that Google Trends config parsing/offline ingestion tests were broken are resolved for the offline/mock dry-run path.
- Earlier notes that `ruff check` failed with about 120 violations are resolved; `ruff check` now passes locally.

## Risks carried forward

- Live providers can change behavior and scaling semantics.
- Synthetic validation does not demonstrate real-world predictive performance.
- MVP BSI reliability/uncertainty values are heuristic labels.
- Geo comparisons remain high risk without local baselines and coverage review.
- Operational use requires legal/privacy/model-risk review and deployment evidence.

## Next milestones before stronger claims

1. Add real browser automation evidence for the dashboard.
2. Run and document Docker/runtime validation.
3. Design live Google Trends validation under legal/provider constraints.
4. Add prospective point-in-time validation before real-world interpretation.
5. Calibrate BSI thresholds and uncertainty with independent review.
6. Replace MVP alert history with production-grade database-backed audit/replay state if operational use is pursued.
