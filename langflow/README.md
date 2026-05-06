# Langflow Workflow

This scaffold orchestrates the synthetic aggregate latent-regime pipeline:

Input Config → Synthetic Data Generator → Preprocessing / Standardization → Ontology Signal Codebook → Adaptive HMM Fit + Predict → Validation Metrics → Report / Output Files → Optional Dashboard Launch Instructions.

## Installation

```bash
pip install -e .[langflow]
```

## Run Langflow

```bash
langflow run
```

## Import

- Open the Langflow UI.
- Import `langflow/behavioral_stress_flow.json`.
- Add custom components from `langflow/custom_components/`.
- Run the flow with `configs/synthetic.yaml`.

If exact Langflow schema behavior changes, the JSON remains a best-effort import scaffold and the Python package remains the source of truth.

## Fallback

```bash
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
```

Warning: Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only.
