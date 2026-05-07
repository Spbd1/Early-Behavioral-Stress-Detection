# Behavioral Stress Regime Detection

Research prototype for detecting latent **aggregate behavioral stress regimes** in synthetic or offline/mock economic-style digital traces using adaptive Hidden Markov Models, ontology-guided signal scaffolding, MVP Behavioral Stress Index (BSI) scoring, and conservative dashboard/reporting utilities.

> **Status box**
>
> | Area | Current status |
> | --- | --- |
> | Project maturity | **Experimental research prototype / MVP** |
> | Validated runnable path | **Synthetic/offline/mock only** |
> | Google Trends ingestion | Experimental; dry-run/mock path is validated locally, live pytrends collection is **not** validated |
> | Production readiness | **Not production-ready** |
> | Recession claims | **Not a recession predictor** and not a production forecasting system |
> | Responsible use | Aggregate research/demo support only; no individual diagnosis, policy automation, or causal claim |

## What this project does

- Generates synthetic aggregate behavioral/economic-style time series with known latent regimes.
- Fits an adaptive Gaussian HMM and writes posterior probabilities, Viterbi paths, transition matrices, and synthetic validation metrics.
- Provides an ontology-guided keyword/signal governance scaffold for aggregate monitoring terms.
- Provides an experimental Google Trends ingestion layer with a deterministic offline/mock `--dry-run` mode.
- Builds a Chrome-friendly browser dashboard payload and static frontend for synthetic/demo artifacts.
- Computes an MVP heuristic BSI payload for research review, with explicit warnings and limitations.
- Emits conservative geo-aware alert/report objects for analyst review in synthetic/demo scenarios.

## What this project does NOT do

- It does **not** predict recessions or certify economic turning points.
- It does **not** provide production monitoring, trading, policy, or intervention recommendations.
- It does **not** infer individual stress, diagnose people, or support individual-level decisions.
- It does **not** validate live Google Trends provider behavior, rate limits, rescaling, or geographic availability.
- It does **not** establish causal effects from observational aggregate digital traces.
- It does **not** implement the full `BSI_DESIGN.md` specification or calibrated production alert thresholds.

## Quick start

Run the validated synthetic path from a fresh checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,dashboard,ingestion]
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
python scripts/run_validation.py --config configs/validation.yaml
ruff check
pytest
```

If editable installation is unavailable in a constrained environment, the Python scripts insert `src/` on `sys.path` where needed. Console entry points such as `behavioral-stress-ingest` and `behavioral-stress-dashboard` require a successful package installation.

## Installation

Core editable install:

```bash
pip install -e .
python -c "import behavioral_stress; print(behavioral_stress.__version__)"
```

Optional extras:

```bash
pip install -e .[dev]
pip install -e .[dashboard]
pip install -e .[ingestion]
pip install -e .[langflow]
pip install -e .[advanced]
```

## Validated synthetic demo

```bash
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
```

Typical outputs are written under `data/synthetic/`:

| Artifact | Purpose |
| --- | --- |
| `observations.csv`, `covariates.csv`, `latent_states.csv` | Synthetic inputs and known latent truth |
| `posterior.csv`, `filtered.csv`, `viterbi_path.csv` | HMM inference outputs |
| `transition_matrix.csv`, `metrics.csv`, `run_metadata.json` | Diagnostics and reproducibility metadata |
| `codebook.csv` | Synthetic ontology/signal metadata |

Validation metrics are meaningful only for the synthetic path with known latent states.

## Offline/mock Google Trends ingestion dry-run

The dry-run mode writes deterministic provider-shaped raw, processed, and metadata artifacts without pytrends or network access:

```bash
behavioral-stress-ingest google-trends --config configs/ingestion/google_trends_sample.yaml --dry-run
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml --dry-run
```

Use the script form when running directly from a checkout without installed console scripts. Live Google Trends collection is experimental and remains unvalidated because provider behavior, sampling/scaling, rate limits, terms, and regional support can change.

## Behavioral Stress Index status

`behavioral_stress.alerting.bsi.BehavioralStressIndex` is an **Implemented MVP BSI** and an MVP heuristic implementation, not the full `BSI_DESIGN.md` specification.

Implemented now:

- Fixed heuristic weights over already-normalized component scores.
- Conservative severity bands, uncertainty labels, reliability score, top contributing signals, component values, limitations, and warnings.
- Explicit experimental and not-recession-prediction language in serialized payloads.

Deferred from the full design:

- Local rolling baselines from raw provider panels.
- Seasonality/holiday/event adjustments.
- Calibrated confidence intervals and threshold approval.
- Volume-aware geographic reliability estimation.
- Transform, weight, calibration, and lineage metadata at production depth.

## Geo-aware alerting/reporting status

Implemented as an MVP research/demo layer:

- Geo metadata, baseline comparison helpers, conservative alert decisions, suppressions, cooldown handling, and report text guardrails.
- JSONL persistent alert history is implemented for MVP replayable decision records.
- In-memory alert history remains the simple default for tests and demos.

Still deferred:

- Production-grade database-backed, auditable, replayable alert state.
- Human approval workflows, alert-threshold governance, incident ownership, and model-risk sign-off.
- Validated geospatial comparability or live provider geography support.

## Browser dashboard / Chrome UI

Build the synthetic/demo dashboard payload:

```bash
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
```

API-backed mode after package installation:

```bash
behavioral-stress-dashboard --host 127.0.0.1 --port 8080 --config configs/production.experimental.yaml
```

Static Chrome-friendly mode:

```bash
python -m http.server 8080 --directory frontend
```

Open `http://127.0.0.1:8080` in Chrome. The browser UI is synthetic/demo-oriented and displays experimental labels, BSI-like demo charts, HMM posterior charts, alerts, top signals, geo comparison placeholders, report export, and warning groups. It is not validated as real-world monitoring.

## Architecture overview

```text
configs/                       YAML configs for synthetic, validation, ingestion, and experimental dashboard paths
scripts/                       Runnable workflow, validation, ingestion, dashboard-data, and healthcheck helpers
src/behavioral_stress/data/     Synthetic generation and preprocessing
src/behavioral_stress/models/   Adaptive HMM and model utilities
src/behavioral_stress/ingestion/ Experimental Google Trends config/cache/client/pipeline
src/behavioral_stress/alerting/ MVP BSI, geo alerting, reports, and alert history
src/behavioral_stress/api/      Dashboard payload builder and stdlib dashboard server
frontend/                      Static browser dashboard assets
tests/                         Offline unit, smoke, schema, and guardrail tests
```

## Data and artifact layout

| Directory | Contents |
| --- | --- |
| `data/synthetic/` | Synthetic demo inputs, model outputs, metrics, and dashboard source artifacts |
| `data/raw/google_trends/` | Raw provider-shaped dry-run/live ingestion batch artifacts |
| `data/processed/google_trends/` | Long-format processed ingestion panels |
| `data/metadata/google_trends/` | Ingestion run metadata and quality flags |
| `frontend/dashboard.json` | Generated static dashboard payload |
| `data/knowledge_base/` | Local project-owned keyword knowledge-base snippets |

Generated data artifacts are demo outputs, not validated real-world measurements.

## Validation status

### Current validation snapshot

Latest local validation on 2026-05-07 in the container:

| Check | Status |
| --- | --- |
| `python -m compileall src scripts tests` | Passed |
| `pytest` | Passed: 50 tests |
| `ruff check` | Passed |
| Synthetic demo command | Passed locally |
| Synthetic validation command | Passed locally |
| Offline/mock Google Trends dry-run | Passed locally via script and module path |
| Dashboard payload build | Passed locally |
| Healthcheck | Passed locally |

Not validated locally:

- Live Google Trends / pytrends ingestion.
- Real browser automation in Chrome.
- Docker runtime.
- Networked deployment, rollback, monitoring integrations, privacy/legal review, and model-risk approval.
- Prospective real-world economic-stress validation or calibrated alert thresholds.

## Limitations and responsible use

- Treat outputs as research/demo artifacts unless independently validated under a documented protocol.
- Google Trends values are sampled and scaled by Google, not absolute query volume.
- Observational aggregate traces are vulnerable to endogeneity, omitted variables, policy feedback, ecological fallacy, sample-selection bias, measurement drift, and time-varying confounding.
- Cross-geography comparisons require local baselines, sample-size review, provider coverage review, and human judgment.
- Signal retirement and alerting outputs are review aids only; they should not automatically delete signals or trigger operational action.
- Keep safety disclaimers visible in downstream materials.

## Development commands

```bash
python -m compileall src scripts tests
pytest
ruff check
python scripts/healthcheck.py
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
python scripts/run_validation.py --config configs/validation.yaml
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml --dry-run
```

Console scripts after package installation:

```bash
behavioral-stress-ingest google-trends --config configs/ingestion/google_trends_sample.yaml --dry-run
behavioral-stress-dashboard --host 127.0.0.1 --port 8080 --config configs/production.experimental.yaml
```

## Roadmap / remaining work

- Validate live provider ingestion only after legal/terms review, provider-code review, rate-limit strategy, replay plan, and drift monitoring are in place.
- Add prospective real-world validation with strict point-in-time data contracts before any operational interpretation.
- Calibrate BSI thresholds and uncertainty through documented model-risk review.
- Add real browser automation and Docker runtime evidence for release/deployment claims.
- Replace MVP alert persistence with production-grade database-backed audit/replay state if moving beyond research demos.
- Continue preserving cautious scientific language and avoiding recession-prediction or production-readiness claims.
