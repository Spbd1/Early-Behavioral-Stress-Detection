from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.ontology.ontology import REQUIRED_CODEBOOK_COLUMNS


def test_generated_shapes_and_codebook():
    data = generate_synthetic_regime_data(n_steps=40, n_states=3, n_features=9, n_covariates=2)
    assert data.observations.shape == (40, 9)
    assert data.covariates.shape == (40, 2)
    assert len(data.latent_states) == 40
    assert set(REQUIRED_CODEBOOK_COLUMNS).issubset(data.codebook.columns)
