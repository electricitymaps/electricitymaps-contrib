from electricitymap.contrib.config.emission_factors import (
    get_emission_factors_with_metadata_all_years,
)


def test_all_emission_factors():
    efs = get_emission_factors_with_metadata_all_years()
    expected_len = 46560
    assert len(efs) == expected_len
