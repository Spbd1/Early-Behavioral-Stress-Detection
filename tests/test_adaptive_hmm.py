import numpy as np

from behavioral_stress.data.preprocessing import standardize_frame
from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


def test_adaptive_hmm_probabilities_and_paths():
    data = generate_synthetic_regime_data(n_steps=80, random_seed=7)
    x = standardize_frame(data.observations).values
    model = AdaptiveHMM(n_states=3, random_seed=7).fit(x)

    assert np.allclose(model.transition_matrix_.sum(axis=1), 1.0)

    filtered, scales, log_likelihood = model.forward(x)
    posterior = model.smooth(x)
    path = model.viterbi(x)

    assert np.allclose(filtered.sum(axis=1), 1.0)
    assert np.allclose(posterior.sum(axis=1), 1.0)
    assert len(path) == len(x)
    assert np.isfinite(log_likelihood)
    assert np.all(scales > 0)

    model.update_transition_matrix(posterior[-20:])
    assert np.allclose(model.transition_matrix_.sum(axis=1), 1.0)
