import numpy as np

from behavioral_stress.data.preprocessing import standardize_frame
from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


def test_forward_normalized_and_viterbi_length():
    data = generate_synthetic_regime_data(n_steps=80, n_states=3, n_features=5)
    x = standardize_frame(data.observations).values
    model = AdaptiveHMM(n_states=3).fit(x)
    alpha, scales, log_likelihood = model.forward(x)
    assert alpha.shape == (80, 3)
    assert np.allclose(alpha.sum(axis=1), 1.0)
    assert np.isfinite(scales).all()
    assert np.isfinite(log_likelihood)
    assert len(model.viterbi(x)) == 80
    posterior = model.smooth(x)
    assert np.allclose(posterior.sum(axis=1), 1.0)


def test_transition_update_rows_sum_to_one():
    data = generate_synthetic_regime_data(n_steps=60, n_states=3, n_features=4)
    x = standardize_frame(data.observations).values
    model = AdaptiveHMM(n_states=3).fit(x)
    updated = model.update_transition_matrix(model.smooth(x))
    assert np.allclose(updated.sum(axis=1), 1.0)
