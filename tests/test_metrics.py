import numpy as np

from behavioral_stress.validation.metrics import binary_classification_metrics


def test_binary_metrics_simple_and_degenerate():
    metrics = binary_classification_metrics(np.array([0, 1, 1, 0]), np.array([0.1, 0.8, 0.7, 0.2]))
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    degenerate = binary_classification_metrics(np.zeros(4), np.array([0.1, 0.2, 0.3, 0.4]))
    assert "roc_auc" in degenerate
