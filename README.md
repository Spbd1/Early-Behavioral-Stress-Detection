# Behavioral Stress Regime Detection

Research prototype for the paper idea **“Detecting Early Behavioral Stress Regimes in Economic Systems: Adaptive Hidden Markov Models, Behavioral Ontologies, and High-Frequency Digital Traces.”**

This repository provides a reproducible Python framework for simulating, detecting, validating, and interpreting latent behavioral stress regimes in aggregate economic/digital traces. The default workflow uses synthetic data with known latent regimes.

## What this project is

- A transparent research framework for latent regime detection.
- A synthetic-data-first testbed for Adaptive Hidden Markov Models (HMMs).
- A modular codebase for ontology-guided signal analysis, validation, and visualization.
- A scaffold for optional Langflow orchestration.

## What this project is not

- It is **not** a validated recession predictor.
- It is **not** a production forecasting system.
- It does **not** infer individual-level stress or diagnose behavior.
- It does **not** make policy recommendations.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For optional Langflow support:

```bash
pip install -e .[langflow]
```

## Run the synthetic demo

```bash
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
```

Outputs are written to `data/synthetic/` and include observations, covariates, ground-truth latent states, posterior probabilities, Viterbi path, and validation metrics.

## Run validation scaffolding

```bash
python scripts/run_validation.py --config configs/validation.yaml
```

The validation package includes synthetic validation, rolling-origin split generation, metrics, and ablation labels for static HMM, adaptive HMM, conditional adaptive HMM, and adaptive HMM plus causal diagnostics.

## Launch the dashboard

```bash
streamlit run src/behavioral_stress/visualization/dashboard.py
```

The dashboard displays the mandatory banner:

> Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only.

## Langflow

See `langflow/README.md`. Langflow is an optional orchestration layer. The core modeling engine remains in the Python package for testability and reproducibility.

## Repository layout

- `src/behavioral_stress/data`: ingestion placeholders, preprocessing, and synthetic data generation.
- `src/behavioral_stress/ontology`: extensible behavioral signal ontology and codebook helpers.
- `src/behavioral_stress/models`: adaptive HMM, conditional HMM prototype, emissions, and baselines.
- `src/behavioral_stress/signal_discovery`: PCA/UMAP exploration, feature screening, and KL drift review diagnostics.
- `src/behavioral_stress/causal`: cautious causal interpretation templates and limitations.
- `src/behavioral_stress/validation`: rolling-origin validation, metrics, ablation, and synthetic validation.
- `src/behavioral_stress/visualization`: Plotly helpers and Streamlit dashboard shell.

## Limitations and Responsible Use

- Aggregate-level inference only.
- No individual behavioral diagnosis.
- No claim of reliable recession prediction.
- Digital trace bias and platform/API bias may affect signals.
- Aggregate digital traces may not be representative of populations or regions.
- Concept drift can invalidate previously useful signals.
- Overfitting and multiple-testing risk are substantial in high-frequency trace discovery.
- False alarms and missed regimes are expected in exploratory prototypes.
- Causal ambiguity is fundamental in observational aggregate data.
- Endogeneity, omitted variables, policy feedback, ecological fallacy, and time-varying confounding must be addressed by separate credible causal designs.
- No policy prescription should be produced without separate causal identification and domain review.

## Tests

```bash
pytest
```
