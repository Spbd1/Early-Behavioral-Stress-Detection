import math

from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


def _row_sums(matrix):
    return [sum(row) for row in matrix]


def _all_close(values, target, tolerance=1e-9):
    return all(abs(value - target) <= tolerance for value in values)


def test_adaptive_hmm_probabilities_and_paths():
    observations = [
        [index / 10.0, (index % 5) / 5.0]
        for index in range(80)
    ]
    model = AdaptiveHMM(n_states=3, random_seed=7).fit(observations)

    assert _all_close(_row_sums(model.transition_matrix_), 1.0)

    filtered, scales, log_likelihood = model.forward(observations)
    posterior = model.smooth(observations)
    path = model.viterbi(observations)

    assert _all_close(_row_sums(filtered), 1.0)
    assert _all_close(_row_sums(posterior), 1.0)
    assert len(path) == len(observations)
    assert math.isfinite(log_likelihood)
    assert all(scale > 0 for scale in scales)

    model.update_transition_matrix(posterior[-20:])
    assert _all_close(_row_sums(model.transition_matrix_), 1.0)
