# Reproducibility guide

## Deterministic mode

- Every experiment config must include `random_seed`.
- Synthetic generator, NumPy, and Python random state are seeded by workflow configuration.
- `configs/production.experimental.yaml` sets deterministic mode explicitly.

## Artifact lineage

Each workflow writes `run_metadata.json` with:

- config path,
- deterministic flag,
- Git commit,
- Python version,
- SHA-256 hashes and sizes for output artifacts,
- derived `model_version` ID.

## Dependency pinning

- `pyproject.toml` defines supported dependency ranges.
- `requirements.lock` is the experimental rebuild baseline.
- For audited runs, rebuild in a clean environment and archive `python -m pip freeze --all` with the run metadata.

## Snapshot discipline

Report snapshot tests should compare stable structure and conservative labels rather than exact floating-point values unless the dependency set and platform are locked.
