# Experimental production hardening guide

This repository remains an **experimental research prototype**. The hardening layer is intended to make synthetic validation runs repeatable, observable, and safer to operate; it does **not** make the system a validated recession predictor.

## Controls added

- **Docker improvements:** non-root container user, explicit runtime environment variables, healthcheck entry point, `.dockerignore`, and a browser-dashboard service in Compose.
- **Environment validation:** required paths and optional secret variables are checked without printing secret values.
- **Config validation:** runtime configs fail closed on missing deterministic seeds, invalid model state counts, invalid output directories, and unsupported synthetic frequencies.
- **CI/CD:** GitHub Actions installs the package, runs health checks, tests, deterministic synthetic smoke tests, frontend payload generation, and Docker build validation.
- **Structured logging:** dependency-free JSON formatter supports operational fields prefixed with `bs_`.
- **Monitoring hooks:** deterministic drift sentinel compares baseline and current means and can recommend rollback review.
- **Health checks:** `scripts/healthcheck.py` aggregates config and environment checks for CI and Docker.
- **Reproducibility guarantees:** deterministic seeds are required, artifacts are hashed, and workflow metadata includes lineage and model-version IDs.
- **Secret management:** the code validates secret variable presence by name and reports only redacted state; secrets must come from the orchestrator or CI secret store.
- **Dependency pinning:** broad package constraints live in `pyproject.toml`; `requirements.lock` captures an experimental baseline for controlled rebuilds.
- **Data lineage:** workflow outputs include artifact SHA-256 hashes, Git commit, Python version, config path, and deterministic mode.
- **Model versioning:** model-version IDs are derived from the lineage manifest.
- **Drift monitoring:** simple mean-shift sentinels are available as guardrails, not as a statistical guarantee.
- **Rollback safety:** production config includes promotion-blocking drift/rollback flags for operators to enforce in deployment tooling.

## Major reliability risks

1. **Provider and sampling instability:** Google Trends and other digital-trace providers can rescale, throttle, omit, or change data semantics. Cache replay and raw artifact retention reduce but do not remove this risk.
2. **Synthetic-to-real gap:** current validation is primarily synthetic. Good synthetic recovery does not prove real-world forecasting, causal validity, or policy usefulness.
3. **Temporal leakage:** any future real-data pipeline must enforce point-in-time feature availability. The current test suite adds guardrails, but leakage can reappear when new joins or reports are added.
4. **Geographic comparability:** country, region, and metro values may have incompatible provider scaling and population/search-volume context. Geo comparisons are displayed as analyst aids only.
5. **Ontology drift:** keyword families can change meaning over time, across countries, or after major events. Human review remains required.
6. **Model misspecification:** HMM assumptions may be wrong, state labels may be unstable, and posterior probabilities are not calibrated probabilities of recession or harm.
7. **Alert fatigue and threshold brittleness:** static BSI thresholds can over-alert or under-alert when baselines shift.
8. **Dependency and platform drift:** Python, OS, and library updates can alter numerical behavior. Pinning and lineage help detect but not eliminate this.
9. **Operational misuse:** dashboard output can be misinterpreted as predictive certainty. UI labels and docs intentionally avoid predictive claims.
10. **Secrets and credentials:** the repository does not store secrets; production operators must use secret stores and rotation procedures.

## Still unsafe for production

- No validated real-world prospective trial.
- No independent statistical audit or model-risk approval.
- No SLA, incident-response staffing, or compliance review.
- No automated rollback controller wired to an orchestrator.
- No privacy/legal review for live provider ingestion in regulated settings.
- No guarantee that alerts are useful, fair, stable, or causally interpretable.
- No individual-level inference support; using this for individuals is prohibited by project scope.

## Remaining research uncertainties

- Whether aggregate search/behavioral traces contain stable early-warning signal after provider rescaling.
- Which keyword ontologies transfer across languages, regions, and economic cycles.
- How to calibrate HMM posterior states against external macroeconomic indicators without leakage.
- How to separate behavioral stress from media cycles, policy announcements, seasonality, and platform changes.
- Which drift metrics best distinguish data issues from meaningful regime changes.
- Whether alert thresholds can be prospectively validated without overfitting historical crises.
