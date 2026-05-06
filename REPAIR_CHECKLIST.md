# Repair Checklist

## Rules

- Do not mark an item DONE unless the relevant verification command passes.
- Do not claim repository success unless all acceptance commands pass.
- Do not add new research features until syntax, packaging, tests, and workflow execution are fixed.
- Do not use fake dependency-free replacements for numpy, pandas, scipy, pandas, scikit-learn, or statsmodels.
- Do not collapse files into one line.
- Keep the project framed as a research prototype, not a validated recession predictor.
- After each repair, record what was wrong, how it was fixed, the files changed, the verification command, and the result.

## Progress Table

| ID | Task | Status | Files changed | What was wrong | How it was fixed | Verification command | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Remove custom build backend | TODO |  |  |  |  |  |  |
| 2 | Remove fake pandas/numpy replacement | TODO |  |  |  |  |  |  |
| 3 | Fix pyproject.toml | TODO |  |  |  |  |  |  |
| 4 | Fix requirements.txt | TODO |  |  |  |  |  |  |
| 5 | Fix Python formatting and syntax | TODO |  |  |  |  |  |  |
| 6 | Fix AdaptiveHMM | TODO |  |  |  |  |  |  |
| 7 | Fix synthetic data generator | TODO |  |  |  |  |  |  |
| 8 | Fix validation metrics | TODO |  |  |  |  |  |  |
| 9 | Fix signal retirement diagnostics | TODO |  |  |  |  |  |  |
| 10 | Fix workflow runner | TODO |  |  |  |  |  |  |
| 11 | Fix Langflow JSON and components | TODO |  |  |  |  |  |  |
| 12 | Fix CLI scripts | TODO |  |  |  |  |  |  |
| 13 | Add dashboard warning and runnable dashboard | TODO |  |  |  |  |  |  |
| 14 | Add Docker/CI sanity | TODO |  |  |  |  |  |  |
| 15 | Run final acceptance commands | TODO |  |  |  |  |  |  |

## Final Acceptance Log

| Command | Status | Result | Notes |
| --- | --- | --- | --- |
| `pip install -e .[dev]` | TODO |  |  |
| `python -m compileall src scripts tests` | TODO |  |  |
| `python -c "import behavioral_stress; print(behavioral_stress.__version__)"` | TODO |  |  |
| `pytest` | TODO |  |  |
| `python scripts/run_synthetic_demo.py --config configs/synthetic.yaml` | TODO |  |  |
| `python scripts/run_validation.py --config configs/validation.yaml` | TODO |  |  |
| `python scripts/export_langflow_demo.py` | TODO |  |  |

## Notes for remaining limitations

- TODO: Record any limitations that remain after repair work is performed.
