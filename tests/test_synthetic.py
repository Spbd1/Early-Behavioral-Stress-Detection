from behavioral_stress.data.synthetic import generate_synthetic_regime_data


def test_synthetic_shapes_and_transition_rows():
    data = generate_synthetic_regime_data(n_steps=50, n_states=3, n_features=6, n_covariates=2)
    assert data.observations.shape == (50, 6)
    assert data.covariates.shape == (50, 2)
    assert data.latent_states.shape == (50,)
    assert data.codebook.shape[0] == 6
    assert data.transition_matrix.shape == (3, 3)
    assert (abs(data.transition_matrix.sum(axis=1) - 1.0) < 1e-10).all()
