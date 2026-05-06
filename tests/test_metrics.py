import numpy as np

from behavioral_stress.validation.metrics import binary_classification_metrics, lead_time


def test_metrics_simple_example():
    metrics = binary_classification_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.8, 0.9]))
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["brier_score"] >= 0.0
    assert lead_time(3, 5) == 2
