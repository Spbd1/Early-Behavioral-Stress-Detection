# Repair Checklist

## Scope

Only these files are in scope for this repair:

- `pyproject.toml`
- `requirements.txt`
- `src/behavioral_stress/models/adaptive_hmm.py`
- `tests/test_adaptive_hmm.py`
- `REPAIR_CHECKLIST.md`

## Formatting Requirements

- `pyproject.toml` must be multi-line TOML with valid sections.
- `requirements.txt` must contain one dependency per line.
- `src/behavioral_stress/models/adaptive_hmm.py` must contain real Python lines for imports, dataclasses, classes, and methods.
- `tests/test_adaptive_hmm.py` must start with valid Python imports and executable pytest tests.
- This checklist must not claim a check passed unless it was run against the current working tree.

## Verified Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Line counts | VERIFIED | Required line-count command reported `pyproject.toml`: 83 lines; `requirements.txt`: 11 lines; `adaptive_hmm.py`: 413 lines; `tests/test_adaptive_hmm.py`: 68 lines. |
| TOML parsing | VERIFIED | `pyproject.toml` parsed with Python's TOML parser and reported project name `behavioral-stress-regime-detection`. |
| Requirements layout | VERIFIED | `requirements.txt` has 11 non-empty dependency lines, one dependency per line. |
| Python parsing | VERIFIED | `python -m compileall src scripts tests` completed successfully. |
| Editable install | BLOCKED | `python -m pip install -e .[dev]` failed while fetching build dependencies because the proxy returned `403 Forbidden` for `/simple/setuptools/`. |
| Focused tests | BLOCKED | `pytest tests/test_adaptive_hmm.py` could not collect tests because NumPy is not installed in this environment after the editable install was blocked. |

## Current Result

The scoped files are stored with real newlines, TOML and requirements formatting checks pass, and Python compilation passes. Full acceptance remains blocked by the environment's inability to install declared dependencies from the package index.

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
