# Behavioral Stress Regime Detection

Research prototype for **“Detecting Early Behavioral Stress Regimes in Economic Systems: Adaptive Hidden Markov Models, Behavioral Ontologies, and High-Frequency Digital Traces.”**

**This project is an experimental research prototype. It is not a validated recession predictor, not a production forecasting system, and not a tool for individual behavioral diagnosis or policy prescription.**

The default demo uses synthetic aggregate-level traces with known latent regimes. The code is intended for cautious synthetic validation of latent regime detection methods, behavioral signal ontologies, and workflow orchestration.

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

The dashboard displays the warning banner, posterior regime probabilities, Viterbi path, synthetic latent truth when available, ontology-coded observations, transition matrix, metrics, and placeholders for KL drift diagnostics.

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

This repository now includes a reusable Google Trends ingestion layer for aggregate,
keyword-level `interest_over_time` data. Install the optional connector dependency before live
collection:

```bash
pip install -e .[ingestion]
```

Run the sample pipeline with either entry point:

```bash
behavioral-stress-ingest google-trends --config configs/ingestion/google_trends_sample.yaml
python scripts/run_google_trends_ingestion.py --config configs/ingestion/google_trends_sample.yaml
```

The ingestion architecture intentionally separates provider coupling from durable artifacts:

- `behavioral_stress.ingestion.config` loads typed YAML settings for keywords, regions,
  historical windows, retries, rate limits, cache TTLs, storage locations, and quality gates.
- `behavioral_stress.ingestion.cache.FileCache` stores content-addressed CSV/JSON cache entries
  by request hash so replayed batches do not repeatedly hit Google Trends.
- `behavioral_stress.ingestion.trends.GoogleTrendsIngestionPipeline` orchestrates historical and
  incremental pulls, regional loops, keyword batching, retry/backoff, rate limiting, raw batch
  writes, processed panel generation, and run metadata.
- `behavioral_stress.ingestion.trends.PytrendsClient` is the default live connector, while tests
  can pass any object that implements the small `TrendsClient` protocol.
- `behavioral_stress.ingestion.logging` emits JSON logs for batch status, cache hits, retry
  attempts, and run IDs.

Raw provider responses are written under `data/raw/google_trends`, processed long-format panels
under `data/processed/google_trends`, and run metadata under `data/metadata/google_trends` by
default. Processed rows contain `date`, `keyword`, `value_raw`, `value_normalized`,
`anchor_value`, `region`, and `timeframe`.

### Ingestion tradeoffs and limitations

Google Trends data is sampled and scaled by Google rather than reported as absolute query volume.
Values are relative to the requested keyword set, region, and time window; low-volume terms may be
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

- The runnable workflow uses synthetic aggregate traces only.
- The model detects latent regimes in synthetic validation; it does not prove recession predictability.
- Observational aggregate digital traces do not identify causal effects by themselves.
- Endogeneity, omitted variables, policy feedback, ecological fallacy, sample-selection bias, measurement drift, and time-varying confounding are serious threats for real data.
- Signal retirement diagnostics flag features for human review only and never automatically delete features.

## Citation placeholder

If this prototype supports a paper or preprint, cite the forthcoming manuscript and this repository version.

## Contributing

Please keep language cautious, preserve the synthetic-data default, add tests for new behavior, and avoid claims of reliable recession prediction, individual diagnosis, or policy prescription.
