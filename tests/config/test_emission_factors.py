from datetime import datetime, timezone

from electricitymap.contrib.config import CO2EQ_PARAMETERS_DIRECT
from electricitymap.contrib.config.emission_factors_lookup import (
    get_emission_factors_with_metadata_all_years,
    get_zone_specific_co2eq_parameter,
)


def test_all_emission_factors(snapshot):
    efs = get_emission_factors_with_metadata_all_years()
    efs = sorted(ef.json(by_alias=True) for ef in efs)
    assert snapshot == efs


def test_get_zone_specific_co2eq_parameter_identical_return():
    zone_key = "AT"
    year = 2024
    dt = datetime(year=year, month=1, day=1, tzinfo=timezone.utc)
    mode = "coal"

    res1 = get_zone_specific_co2eq_parameter(
        co2eq_parameters=CO2EQ_PARAMETERS_DIRECT,
        zone_key=zone_key,
        key="emissionFactors",
        sub_key=mode,
        dt=dt,
    )

    res2 = get_zone_specific_co2eq_parameter(
        co2eq_parameters=CO2EQ_PARAMETERS_DIRECT,
        zone_key=zone_key,
        key="emissionFactors",
        sub_key=mode,
        dt=dt,
        metadata=True,
    )

    assert res1["value"] == res2["value"]
