# Troubleshooting guide

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Healthcheck reports `degraded` | Config warning/error or missing path | Run `python scripts/healthcheck.py` and fix the reported path. |
| Dashboard shows no charts | Missing `posterior.csv` | Run the synthetic workflow and rebuild `frontend/dashboard.json`. |
| Chrome blocks data when opened as a file | Browser `file://` fetch restrictions | Serve with `behavioral-stress-dashboard` or `python -m http.server`. |
| Tests differ across machines | Dependency/platform drift | Use `requirements.lock`, record Python version, and compare lineage metadata. |
| Too many alerts | Threshold brittleness or shifted baseline | Review drift report and thresholds; do not automate action from alerts. |
| Geo table looks inconsistent | Provider scaling or synthetic fallback | Treat geo comparison as qualitative analyst context only. |
