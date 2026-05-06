FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
CMD ["python", "scripts/run_synthetic_demo.py", "--config", "configs/synthetic.yaml"]
