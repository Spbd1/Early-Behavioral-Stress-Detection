# Langflow orchestration layer

Langflow is optional and should be used as an experimentation/orchestration layer rather than the core modeling engine.

Proposed flow:

`Input Config → Data Loader → Preprocessing → Ontology Signal Generator → Adaptive HMM → Validation Metrics → Visualization / Report`

Install optional dependencies with `pip install -e .[langflow]`, then import `behavioral_stress_flow.json` or adapt the custom component stubs in `custom_components/`.
