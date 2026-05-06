# Operational playbooks

## Config validation failure

1. Run `python scripts/healthcheck.py`.
2. Inspect config issue paths in the JSON output.
3. Fix missing `random_seed`, invalid state counts, invalid synthetic frequency, or missing output directory.
4. Re-run the synthetic smoke test.

## Drift warning

1. Treat warning as a deployment blocker until reviewed.
2. Compare raw artifacts, provider metadata, and keyword family changes.
3. Confirm whether drift is a provider/data-quality issue or a true synthetic scenario change.
4. Keep serving the previous model version unless a human reviewer approves promotion.

## Dashboard data missing

1. Run `python scripts/run_synthetic_demo.py --config configs/production.experimental.yaml`.
2. Run `python scripts/build_frontend_data.py --config configs/production.experimental.yaml`.
3. Refresh Chrome with cache disabled.

## Secret rotation

1. Rotate secrets in the orchestrator or CI secret store, not in Git.
2. Restart the service so the new environment variable is visible.
3. Run the environment validator and confirm output is redacted.

## Rollback

1. Stop promotion of the candidate version.
2. Restore the previous artifact directory and `run_metadata.json`.
3. Confirm healthcheck and dashboard payload build succeed.
4. Record the failed model version and rollback reason in the experiment log.
