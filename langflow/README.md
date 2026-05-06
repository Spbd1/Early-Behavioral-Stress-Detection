# Langflow Workflow

This scaffold documents a Langflow import for the synthetic aggregate behavioral-stress research pipeline:

`config` → `synthetic_data` → `preprocessing` → `ontology` → `adaptive_hmm` → `metrics` → `report`

The custom components are thin wrappers around the existing package functions/classes. They are not a second implementation of the modeling workflow.

## Install Langflow extras

From the repository root, install the project with the Langflow optional dependencies:

```bash
pip install -e .[langflow]
```

## Start Langflow

Run Langflow from the same environment:

```bash
langflow run
```

## Import the scaffold flow

1. Open the Langflow UI shown by `langflow run`.
2. Import `langflow/behavioral_stress_flow.json`.
3. Add custom components from `langflow/custom_components/`:
   - `synthetic_data_component.py`
   - `preprocessing_component.py`
   - `ontology_signal_component.py`
   - `adaptive_hmm_component.py`
   - `validation_metrics_component.py`
   - `report_component.py`
4. Use `configs/synthetic.yaml` for the config input.

Langflow component APIs can change across releases, so this file is a scaffold for wiring the package workflow in the UI. The source of truth remains the Python package and scripts.

## Fallback command

If Langflow import or component loading is unavailable, run the equivalent package workflow directly:

```bash
python scripts/run_synthetic_demo.py --config configs/synthetic.yaml
```

Warning: Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only.
