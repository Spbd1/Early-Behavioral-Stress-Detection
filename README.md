# Behavioral Stress Regime Detection

Research prototype for **“Detecting Early Behavioral Stress Regimes in Economic Systems: Adaptive Hidden Markov Models, Behavioral Ontologies, and High-Frequency Digital Traces.”**

**This project is an experimental research prototype. It is not a validated recession predictor, not a production forecasting system, and not a tool for individual behavioral diagnosis or policy prescription.**

The validated runnable demo remains synthetic: it uses synthetic aggregate-level traces with known latent regimes. The code is intended for cautious synthetic validation of latent regime detection methods, behavioral signal ontologies, and workflow orchestration. Real Google Trends ingestion is experimental and is not part of the validated default demo.

## What it is

- A Python research prototype for synthetic latent regime detection.
- A synthetic-data-first workflow using aggregate-level traces.
- A modular implementation of an Adaptive Gaussian HMM with stable filtering, smoothing, and Viterbi decoding.
- A behavioral ontology/codebook scaffold for aggregate signals.
- CLI, Streamlit, Docker, and Langflow scaffolds.

## What it is not

- Not a validated recession predictor.
- Not a production forecasting system.
- Not a tool for individual-level stress inference or diagnosis.
- Not a source of policy recommendations.
- Not a causal identification design for real-world interventions.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -c "import behavioral_stress; print(behavioral_stress.__version__)"
```

Optional extras:

```bash
pip install -e .[dashboard]
pip install -e .[langflow]
pip install -e .[advanced]
pip install -e .[dev]
```

## Synthetic demo

```bash
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
```

Expected outputs:

- `data/synthetic/observations.csv`
- `data/synthetic/covariates.csv`
- `data/synthetic/latent_states.csv`
- `data/synthetic/codebook.csv`
- `data/synthetic/posterior.csv`
- `data/synthetic/filtered.csv`
- `data/synthetic/viterbi_path.csv`
- `data/synthetic/transition_matrix.csv`
- `data/synthetic/metrics.csv`
- `data/synthetic/run_metadata.json`

## Validation

```bash
python scripts/run_validation.py --config configs/validation.yaml
```

Validation metrics are designed for synthetic data with known latent states and should not be interpreted as real-world recession prediction performance.

## Dashboard

```bash
python scripts/build_dashboard.py --config configs/default.yaml
streamlit run src/behavioral_stress/visualization/dashboard.py
```

The validated dashboard path is synthetic/demo-only. It displays the warning banner, posterior regime probabilities, Viterbi path, synthetic latent truth when available, ontology-coded observations, transition matrix, metrics, and placeholders for KL drift diagnostics. It must not be read as validated real-world monitoring.

## Langflow workflow

```bash
pip install -e .[langflow]
langflow run
python scripts/export_langflow_demo.py
```

Then import `langflow/behavioral_stress_flow.json` and add custom components from `langflow/custom_components/`. See `langflow/README.md` for details. The pure-Python fallback runner is `behavioral_stress.workflows.synthetic_workflow.run_synthetic_workflow`.

## Ontology-guided keyword generation

The repository includes a local-first, ontology-guided keyword workflow for maintaining
behavioral stress monitoring terms by country, state/province/region, city, or metro. The
workflow combines a controlled keyword ontology, a lightweight local RAG retriever, reviewable
keyword candidates, geo metadata with stable codes where possible, human approval gates,
deduplication, semantic grouping, version history, retirement, and drift-review flags.

The local RAG layer reads project-owned snippets from `data/knowledge_base/behavioral_stress_keyword_kb.jsonl`
and is used only for explanation and grounding. It must not decide alerts or bypass reviewer
approval. See `docs/ontology_guided_keyword_generation.md` for the schema, hallucination risks,
mitigations, and provider-geography limitations.


## Google Trends ingestion

**Experimental status:** Real Google Trends ingestion is an experimental, optional research path. It is not part of the validated synthetic demo and should not be treated as production-ready data collection.

This repository includes a Google Trends ingestion layer for aggregate, keyword-level
`interest_over_time` data, but live provider behavior remains unvalidated and subject to provider changes. Install the optional connector dependency before experimental live collection:

```bash
pip install -e .[ingestion]
```

Run the experimental sample pipeline with either entry point. Use `--dry-run` for deterministic offline/mock artifact generation that does not require pytrends or network access:

```bash
behavioral-stress-ingest google-trends --config configs/ingestion/google_trends_sample.yaml --dry-run
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml --dry-run
```

The experimental ingestion architecture intentionally separates provider coupling from durable artifacts:

- `behavioral_stress.ingestion.config` loads typed YAML settings for keywords, regions,
  historical windows, retries, rate limits, cache TTLs, storage locations, and quality gates.
- `behavioral_stress.ingestion.cache.FileCache` stores content-addressed CSV/JSON cache entries
  by request hash so replayed batches do not repeatedly hit Google Trends.
- `behavioral_stress.ingestion.trends.GoogleTrendsIngestionPipeline` orchestrates historical and
  incremental pulls, regional loops, keyword batching, retry/backoff, rate limiting, raw batch
  writes, processed panel generation, and run metadata.
- `behavioral_stress.ingestion.trends.PytrendsClient` is the default live connector and raises
  a clear optional-dependency error if pytrends is missing. `MockTrendsClient` backs dry-run
  ingestion, and tests can pass any object that implements the small `TrendsClient` protocol.
- `behavioral_stress.ingestion.logging` emits JSON logs for batch status, cache hits, retry
  attempts, and run IDs.

Raw provider responses are schema-checked and written under `data/raw/google_trends`, processed long-format panels
under `data/processed/google_trends`, and validated run metadata under `data/metadata/google_trends` by
default. Processed rows contain `date`, `keyword`, `value_raw`, `value_normalized`,
`anchor_value`, `region`, and `timeframe`.

### Ingestion tradeoffs and limitations

Google Trends data is sampled and scaled by Google rather than reported as absolute query volume.
Values are relative to the requested keyword set, region, and time window, so raw values should not be naively compared across regions; low-volume terms may be
rounded to zero or omitted; repeated pulls can change; long windows may be returned at coarser
resolution; and Google can throttle, block, or alter unofficial access behavior. The pipeline
therefore treats Google Trends as a noisy aggregate research signal, not a stable measurement
system.

The connector uses pytrends because it is widely used and lightweight, but it is unofficial and can
break when Google changes web behavior. The `TrendsClient` protocol keeps this replaceable by a
commercial or internal provider if reliability, legal review, or support requirements change.

Normalization consistency is mitigated by forcing batches to include an anchor keyword whenever one
is configured. Non-anchor series are scaled relative to the anchor within each batch, and metadata
records anchor values and validation issues. This reduces—but does not eliminate—cross-batch drift,
because the anchor itself is still a Google-rescaled sampled series. Additional mitigation comes
from cache-backed replay, overlap-based incremental updates, raw artifact retention, and explicit
quality flags for sparse, missing, nonpositive-anchor, or high-variation anchor batches.

## Behavioral Stress Index (BSI) status

The implemented `behavioral_stress.alerting.bsi.BehavioralStressIndex` is an **Implemented MVP BSI**, not the complete design in `BSI_DESIGN.md`. It accepts already-normalized component scores and returns a conservative research/demo payload containing `score`, `severity_band`, `uncertainty_band`, MVP `reliability_score`, `top_contributing_signals`, `limitations`, `warnings`, an `implementation_label`, and component values.

Implemented in the MVP: fixed heuristic weighting of HMM posterior, anomaly strength, signal breadth, persistence, trend acceleration, data quality, drift confidence, geographic confidence; conservative severity bands; top contributors; safety limitations and warnings.

Deferred from the fuller design: local rolling baselines from raw provider panels, seasonality/holiday/event adjustment, calibrated confidence intervals, volume-aware geographic reliability estimation, persistent alert history, and transform/weight/calibration lineage metadata. `BSI_DESIGN.md` remains a design-only specification. The MVP BSI is experimental aggregate monitoring support, **not a recession prediction mechanism**.

## Docker

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build research-demo
```

Dashboard:

```bash
docker compose -f docker/docker-compose.yml up --build dashboard
```

Optional Langflow service is behind the `langflow` profile because Langflow is comparatively heavy:

```bash
docker compose -f docker/docker-compose.yml --profile langflow up --build langflow
```

## Repository structure

```text
configs/                  YAML configurations
data/                     synthetic/raw/processed data directories
langflow/                 flow JSON plus custom component wrappers
scripts/                  command-line entry points
src/behavioral_stress/    package source
tests/                    pytest tests
```

## Limitations and responsible use

- The validated runnable workflow uses synthetic aggregate traces only.
- Real Google Trends ingestion is experimental and not part of the validated demo path.
- The model detects latent regimes in synthetic validation; it does not prove real-world predictive performance.
- Observational aggregate digital traces do not identify causal effects by themselves.
- Endogeneity, omitted variables, policy feedback, ecological fallacy, sample-selection bias, measurement drift, and time-varying confounding are serious threats for real data.
- Signal retirement diagnostics flag features for human review only and never automatically delete features.

## Citation placeholder

If this prototype supports a paper or preprint, cite the forthcoming manuscript and this repository version.

## Contributing

Please keep language cautious, preserve the synthetic-data default, add tests for new behavior, and avoid claims of reliable recession prediction, individual diagnosis, or policy prescription.

## Experimental production hardening and browser UI

The repository includes a Chrome-friendly browser dashboard plus an operational hardening layer for **experimental** deployments. The validated browser-dashboard data path remains synthetic/demo-only. These controls improve repeatability and observability, but they do not validate real-world monitoring or predictive power.

### Browser dashboard

API-backed mode:

```bash
python scripts/run_synthetic_demo.py --config configs/production.experimental.yaml
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
behavioral-stress-dashboard --host 127.0.0.1 --port 8080 --config configs/production.experimental.yaml
```

Open Chrome at `http://127.0.0.1:8080`.

Static mode:

```bash
python scripts/build_frontend_data.py --config configs/production.experimental.yaml --output frontend/dashboard.json
python -m http.server 8080 --directory frontend
```

The UI supports country, region/province/state, city/metro, time-range, and keyword-family filters; BSI-like synthetic demo and HMM posterior charts; alert timeline; top contributing signals; geo comparison table/map placeholder; report viewer; data-quality warnings; drift warnings; geo reliability warnings; and report export. It is intentionally labeled as experimental, is currently synthetic/demo-oriented, and avoids claims of recession prediction. Static mode uses generated `frontend/dashboard.json` and does not require the dashboard API backend, but Chrome users should serve the `frontend/` directory with a static file server rather than opening `index.html` directly from `file://` because local fetches can be blocked by the browser.

### Operations docs

- Production hardening guide: `docs/production_hardening.md`
- Deployment runbook: `docs/operations/deployment.md`
- Operational playbooks: `docs/operations/playbooks.md`
- Troubleshooting guide: `docs/operations/troubleshooting.md`
- Reproducibility guide: `docs/reproducibility/reproducibility_guide.md`

### Health and validation

```bash
python scripts/healthcheck.py
pytest tests/test_ops_hardening.py tests/test_data_validation_suite.py tests/test_frontend_static.py
```
