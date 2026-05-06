from behavioral_stress.data.synthetic import (
    SyntheticRegimeData,
    generate_synthetic_regime_data,
)
from behavioral_stress.ontology.ontology import REQUIRED_CODEBOOK_COLUMNS


def test_generated_shapes_codebook_metadata_and_non_empty_columns():
    data = generate_synthetic_regime_data(
        n_steps=40, n_states=3, n_features=9, n_covariates=2
    )

    assert isinstance(data, SyntheticRegimeData)
    assert data.observations.shape == (40, 9)
    assert data.covariates.shape == (40, 2)
    assert len(data.latent_states) == 40
    assert set(REQUIRED_CODEBOOK_COLUMNS).issubset(data.codebook.columns)
    assert isinstance(data.metadata, dict)
    assert (
        data.metadata["ontology_mapping"]["level_1"]
        == "immediate elastic discretionary contraction"
    )
    assert (
        data.metadata["ontology_mapping"]["level_2"]
        == "deferred/semi-essential adjustment"
    )
    assert data.metadata["ontology_mapping"]["level_3"] == (
        "substitution/persistence/micro-luxury response"
    )
    assert not data.observations.isna().all(axis=0).any()
    assert not data.covariates.isna().all(axis=0).any()
    assert not data.codebook.isna().all(axis=0).any()
