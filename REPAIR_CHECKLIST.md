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
| 1 | Remove custom build backend | DONE | `pyproject.toml`; `build_backend.py` | The project used an in-repository `build_backend` PEP 517/660 implementation with empty build requirements instead of a standard backend. | Deleted `build_backend.py` and changed `pyproject.toml` to use `setuptools.build_meta` with normal setuptools/wheel build requirements. | `test ! -e build_backend.py && python -m compileall src/behavioral_stress/data/synthetic.py src/behavioral_stress/data/preprocessing.py src/behavioral_stress/models/adaptive_hmm.py src/behavioral_stress/ontology/ontology.py src/behavioral_stress/ontology/signal_codebook.py src/behavioral_stress/workflows/synthetic_workflow.py` | PASS: `build_backend.py` is absent and the touched Python modules compile. | `pyproject.toml` now declares package discovery under `src`. |
| 2 | Remove fake pandas/numpy replacement | DONE | `pyproject.toml`; `src/behavioral_stress/simple_frame.py`; `src/pandas.py`; `src/numpy.py`; `src/behavioral_stress/data/synthetic.py`; `src/behavioral_stress/data/preprocessing.py`; `src/behavioral_stress/models/adaptive_hmm.py`; `src/behavioral_stress/ontology/ontology.py`; `src/behavioral_stress/ontology/signal_codebook.py`; `src/behavioral_stress/workflows/synthetic_workflow.py` | `src/behavioral_stress/simple_frame.py` provided local `DataFrame`, `Series`, `Vector`, and `Matrix` stand-ins, while `src/pandas.py` and `src/numpy.py` shadowed real third-party packages. | Deleted `simple_frame.py`, `src/pandas.py`, and `src/numpy.py`; replaced their use with real pandas DataFrame/Series objects and NumPy arrays; and declared real scientific dependencies in `pyproject.toml`. | `rg -n "build_backend|simple_frame|dependency-free|dependency free|compatibility shim|Tiny pandas|Tiny NumPy" pyproject.toml src/behavioral_stress src/pandas.py src/numpy.py 2>/dev/null || true; test ! -e src/pandas.py && test ! -e src/numpy.py && test ! -e src/behavioral_stress/simple_frame.py` | PASS: no code or packaging references to the fake stack remain, and `src/pandas.py`, `src/numpy.py`, and `simple_frame.py` are absent. | Checklist text still mentions the removed fake stack for audit context only. |
| 3 | Fix pyproject.toml | DONE | `pyproject.toml`; `REPAIR_CHECKLIST.md` | `pyproject.toml` did not declare the full required runtime, development, Langflow, and advanced optional dependency groups for normal setuptools packaging. | Rewrote `pyproject.toml` as standard TOML using `setuptools.build_meta`, unpinned required dependencies, optional dependency groups, `src` package discovery, and basic pytest configuration. | `python -m pip install -e .[dev]` | PASS: user reported `python -m pip install -e .[dev]` passed. | Verification was run by the user after the packaging repair. |
| 4 | Fix requirements.txt | TODO | `requirements.txt`; `REPAIR_CHECKLIST.md` | `requirements.txt` contained comments describing optional installs instead of the required one-dependency-per-line baseline. | Replaced the file contents with the exact requested dependency baseline, one package per line. | `python -m pip install -r requirements.txt` | pending until I run it |  |
| 5 | Fix Python formatting and syntax | PENDING USER VERIFICATION | `src/behavioral_stress/models/adaptive_hmm.py`; `tests/test_adaptive_hmm.py`; `REPAIR_CHECKLIST.md` | `AdaptiveHMM` was a facade with incomplete HMM behavior, two-dimensional-only input handling, and Viterbi decoding based on posterior argmax rather than log-space dynamic programming. | Rewrote the implementation with clear docstrings, NumPy/SciPy numerical operations, KMeans initialization, scaled forward/backward recursions, normalized filtering/smoothing outputs, and log-space Viterbi; tightened the focused test assertions. | `pytest tests/test_adaptive_hmm.py` | pending until I run it | Not marked DONE until the requested verification command passes. |
| 6 | Fix AdaptiveHMM | PENDING USER VERIFICATION | `src/behavioral_stress/models/adaptive_hmm.py`; `tests/test_adaptive_hmm.py`; `REPAIR_CHECKLIST.md` | The model lacked a complete Gaussian HMM implementation: no true log-space Viterbi path search, no online filter method, one-dimensional observations were rejected, and normalization guarantees were not enforced consistently. | Implemented Gaussian emissions with numerical epsilons, scaled forward/backward recursions, normalized smoothed and filtered probabilities, adaptive row-normalized transition updates, `filter_online`, finite likelihood handling, and focused checks for probability row sums, Viterbi length, transition normalization, and finite likelihood. | `pytest tests/test_adaptive_hmm.py` | pending until I run it | Not marked DONE until the requested verification command passes. |
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
