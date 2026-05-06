# Deployment and browser UI runbook

## Local deterministic run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/healthcheck.py
python scripts/run_synthetic_demo.py --config configs/production.experimental.yaml
python scripts/build_frontend_data.py --config configs/production.experimental.yaml
behavioral-stress-dashboard --host 127.0.0.1 --port 8080 --config configs/production.experimental.yaml
```

Open Chrome at `http://127.0.0.1:8080`.

## Static browser-only mode

```bash
python scripts/run_synthetic_demo.py --config configs/production.experimental.yaml
python scripts/build_frontend_data.py --config configs/production.experimental.yaml --output frontend/dashboard.json
python -m http.server 8080 --directory frontend
```

Open Chrome at `http://127.0.0.1:8080`. The UI first tries `/api/dashboard.json` and then falls back to `frontend/dashboard.json`.

## Docker Compose

```bash
docker compose -f docker/docker-compose.yml --profile dashboard up --build dashboard
```

The dashboard is served on `http://localhost:8080`.

## Promotion checklist

1. Confirm `scripts/healthcheck.py` returns acceptable config/environment status.
2. Confirm CI passed tests, synthetic smoke run, frontend payload generation, and Docker build.
3. Review `data/synthetic/run_metadata.json` for `model_version`, lineage hashes, and Git commit.
4. Review drift sentinels before promoting any new model artifacts.
5. Keep the previous model artifacts available until the new version is manually accepted.
