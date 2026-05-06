# Repair Checklist

## Scope

Only these files are in scope for this repair:

- `pyproject.toml`
- `requirements.txt`
- `src/behavioral_stress/models/adaptive_hmm.py`
- `tests/test_adaptive_hmm.py`
- `REPAIR_CHECKLIST.md`

## Formatting Requirements

- `pyproject.toml` must be multi-line TOML with valid sections.
- `requirements.txt` must contain one dependency per line.
- `src/behavioral_stress/models/adaptive_hmm.py` must contain real Python lines for imports, dataclasses, classes, and methods.
- `tests/test_adaptive_hmm.py` must start with valid Python imports.
- This checklist must not claim a check passed unless it was run against the current working tree.

## Verified Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Line counts | VERIFIED | `pyproject.toml`: 37; `requirements.txt`: 11; `adaptive_hmm.py`: 380; `tests/test_adaptive_hmm.py`: 34; `REPAIR_CHECKLIST.md`: 32 before this rewrite. |
| TOML parsing | VERIFIED | Parsed `pyproject.toml` with the installed `tomli` parser under Python 3.10. |
| Requirements layout | VERIFIED | Confirmed each `requirements.txt` dependency is on its own non-empty line. |
| Test import header | VERIFIED | Confirmed `tests/test_adaptive_hmm.py` starts with `import math` and the `AdaptiveHMM` import. |
| Python parsing | VERIFIED | `python -m compileall src/behavioral_stress/models/adaptive_hmm.py tests/test_adaptive_hmm.py` completed successfully. |
| Focused tests | VERIFIED | `pytest tests/test_adaptive_hmm.py` completed successfully with one passing test. |

## Current Result

The scoped files are stored with real newlines, and the verification commands above were run against this working tree.
