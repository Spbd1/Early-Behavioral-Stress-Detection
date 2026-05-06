import math

import numpy as np
import pytest

from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


def _synthetic_observations() -> np.ndarray:
    rng = np.random.default_rng(123)
    low = rng.normal(loc=-2.0, scale=0.25, size=(30, 2))
    middle = rng.normal(loc=0.0, scale=0.25, size=(30, 2))
    high = rng.normal(loc=2.0, scale=0.25, size=(30, 2))
    return np.vstack([low, middle, high])


def test_model_fits_synthetic_numpy_data_and_outputs_are_normalized() -> None:
    observations = _synthetic_observations()
    model = AdaptiveHMM(n_states=3, random_seed=7, max_iter=5).fit(observations)

    assert model.means_.shape == (3, 2)
    assert np.allclose(model.transition_matrix_.sum(axis=1), 1.0)
    assert math.isfinite(model.log_likelihood_)

    forward_result = model.forward(observations)
    posterior = model.smooth(observations)
    path = model.viterbi(observations)

    assert np.allclose(forward_result.probabilities.sum(axis=1), 1.0)
    assert np.all(forward_result.scales > 0.0)
    assert math.isfinite(forward_result.log_likelihood)
    assert np.allclose(posterior.sum(axis=1), 1.0)
    assert len(path) == len(observations)


def test_transition_matrix_rows_sum_before_and_after_update() -> None:
    observations = _synthetic_observations()
    model = AdaptiveHMM(n_states=3, random_seed=7, max_iter=5).fit(observations)

    assert np.allclose(model.transition_matrix_.sum(axis=1), 1.0)

    posterior = model.smooth(observations)
    updated = model.update_transition_matrix(posterior[-20:])

    assert np.allclose(updated.sum(axis=1), 1.0)
    assert np.allclose(model.transition_matrix_.sum(axis=1), 1.0)


def test_as_matrix_handles_numpy_arrays_and_rejects_none() -> None:
    two_dimensional = np.array([[1.0, 2.0], [3.0, 4.0]])
    one_dimensional = np.array([1.0, 2.0, 3.0])

    converted_two_dimensional = AdaptiveHMM._as_matrix(two_dimensional)
    converted_one_dimensional = AdaptiveHMM._as_matrix(one_dimensional)

    assert converted_two_dimensional.shape == (2, 2)
    assert converted_one_dimensional.shape == (3, 1)

    with pytest.raises(ValueError, match="must not be None"):
        AdaptiveHMM._as_matrix(None)


def test_as_matrix_does_not_use_ambiguous_numpy_truth_value() -> None:
    observations = np.array([[0.0], [1.0], [2.0]])

    converted = AdaptiveHMM._as_matrix(observations)

    assert converted.shape == (3, 1)
