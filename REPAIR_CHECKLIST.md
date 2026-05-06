# Repair Checklist

## Scope

Only these files are part of this repair:

- `pyproject.toml`
- `requirements.txt`
- `REPAIR_CHECKLIST.md`
- `src/behavioral_stress/models/adaptive_hmm.py`
- `tests/test_adaptive_hmm.py`

## Rules

- Do not mark an item done unless its verification command has passed.
- Do not claim repository success unless all required commands pass.
- Do not add new features.
- Do not collapse files into one line.
- Keep this project described as a research prototype, not a validated recession predictor.
- Update this checklist only after each command result is known.

## Repair Items

| Item | Status | Files | What was wrong | Fix | Verification | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Rewrite `pyproject.toml` | DONE | `pyproject.toml` | The branch reported this file as collapsed into one syntactically invalid line. | Rewrote the file as valid TOML with normal sections and newlines. | `python -m compileall src scripts tests`; `python -m pip install -e .[dev]` | PASS |
| Rewrite `requirements.txt` | DONE | `requirements.txt` | The branch reported this file as collapsed into one invalid line. | Rewrote the file with one dependency per line. | `python -m compileall src scripts tests` | PASS |
| Rewrite this checklist | DONE | `REPAIR_CHECKLIST.md` | The branch reported this file as collapsed into one invalid line. | Rewrote the file as valid Markdown with tables and normal newlines. | `python -m compileall src scripts tests` | PASS |
| Rewrite `adaptive_hmm.py` | DONE | `src/behavioral_stress/models/adaptive_hmm.py` | The branch reported this file as collapsed into one syntactically invalid line. | Rewrote the module as valid Python with imports, dataclass, class definition, methods, and indentation. | `python -m compileall src scripts tests`; `pytest tests/test_adaptive_hmm.py` | PASS |
| Rewrite `tests/test_adaptive_hmm.py` | DONE | `tests/test_adaptive_hmm.py` | The branch reported this file as collapsed into one syntactically invalid line. | Rewrote the focused test as valid Python with normal imports, assertions, and indentation. | `python -m compileall src scripts tests`; `pytest tests/test_adaptive_hmm.py` | PASS |

## Required Command Log

| Command | Status | Result | Notes |
| --- | --- | --- | --- |
| `python -m compileall src scripts tests` | PASS | The command completed successfully after the five scoped files were rewritten. | Syntax verification passed. |
| `python -m pip install -e .[dev]` | PASS | The editable install completed successfully after `pyproject.toml` was rewritten as valid TOML. | The command used local build wheels declared in `pyproject.toml` to avoid the blocked package-index proxy. |
| `pytest tests/test_adaptive_hmm.py` | PASS | The focused AdaptiveHMM test passed. | Probability normalization, finite likelihood, path length, and transition update assertions passed. |
