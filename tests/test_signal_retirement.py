import numpy as np

from behavioral_stress.signal_discovery.retirement import flag_signal_retirement, kl_divergence_gaussian


def test_kl_and_retirement_flag():
    rng = np.random.default_rng(42)
    old = rng.normal(size=50)
    new = rng.normal(0.5, 1.2, size=50)
    score = kl_divergence_gaussian(old, new)
    result = flag_signal_retirement(old, new, threshold=0.01)
    assert np.isfinite(score)
    assert score >= 0
    assert isinstance(result["flag_for_review"], bool)
    assert "kl_divergence" in result
