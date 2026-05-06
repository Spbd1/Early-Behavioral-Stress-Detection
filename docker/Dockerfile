FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BEHAVIORAL_STRESS_ENV=experimental

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md requirements.txt requirements.lock ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY langflow ./langflow
COPY frontend ./frontend
COPY docs ./docs

RUN python -m pip install --upgrade pip \
    && python -m pip install -e . \
    && python scripts/healthcheck.py

RUN mkdir -p /app/data && chown -R app:app /app
USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python scripts/healthcheck.py || exit 1

CMD ["python", "scripts/run_synthetic_demo.py", "--config", "configs/synthetic.yaml"]
