import numpy as np

from behavioral_stress.signal_discovery.retirement import flag_signal_retirement, histogram_kl_divergence


def test_kl_retirement_finite():
    rng = np.random.default_rng(42)
    old = rng.normal(0, 1, 100)
    new = rng.normal(0.2, 1, 100)
    kl_value = histogram_kl_divergence(old, new)
    result = flag_signal_retirement(old, new, retirement_threshold=10.0)
    assert np.isfinite(kl_value)
    assert "flag_for_review" in result
