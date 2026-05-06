FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY langflow ./langflow
RUN pip install --no-cache-dir -e .[dashboard]
CMD ["python", "scripts/run_synthetic_demo.py", "--config", "configs/synthetic.yaml"]
