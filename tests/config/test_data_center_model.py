from unittest.mock import patch

import pytest
from pydantic.v1 import ValidationError

from electricitymap.contrib.config.data_center_model import DataCenter, DataCenters
from electricitymap.contrib.types import ZoneKey

VALID_ZONE_KEY = ZoneKey("DE")

FR_ZONE_KEY = ZoneKey("FR")
INVALID_ZONE_KEY = ZoneKey("INVALID")

MOCK_ZONES_CONFIG = {VALID_ZONE_KEY: {}, FR_ZONE_KEY: {}}


def make_data_center(
    provider: str = "AWS",
    lonlat: tuple[float, float] = (10.0, 50.0),
    displayName: str = "EU West",
    region: str = "eu-west-1",
    zoneKey: ZoneKey = VALID_ZONE_KEY,
    operationalSince: str | None = None,
    operationalUntil: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> DataCenter:
    return DataCenter(
        provider=provider,
        lonlat=lonlat,
        displayName=displayName,
        region=region,
        zoneKey=zoneKey,
        operationalSince=operationalSince,
        operationalUntil=operationalUntil,
        status=status,
        source=source,
    )


@pytest.fixture(autouse=True)
def _mock_zones_config():
    with patch(
        "electricitymap.contrib.config.data_center_model.ZONES_CONFIG",
        MOCK_ZONES_CONFIG,
        create=True,
    ), patch(
        "electricitymap.contrib.config.ZONES_CONFIG",
        MOCK_ZONES_CONFIG,
    ):
        yield


class TestDataCenterID:
    def test_id_format(self):
        dc = make_data_center()
        assert dc.ID == "AWS-eu-west-1"


class TestStringNotEmpty:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {"provider": ""},
            {"region": ""},
            {"displayName": ""},
            {"provider": "   "},
            {"region": "   "},
            {"displayName": "   "},
        ],
    )
    def test_empty_or_whitespace_rejected(self, kwargs: dict[str, str]):
        with pytest.raises(ValidationError, match="Value must be a non-empty string"):
            make_data_center(**kwargs)  # type: ignore[arg-type]

    def test_valid_strings_accepted(self):
        make_data_center(provider="valid", region="valid", displayName="valid")


class TestLonlatValid:
    def test_valid_lonlat(self):
        make_data_center(lonlat=(0.0, 0.0))

    def test_boundary_values(self):
        make_data_center(lonlat=(-180.0, -90.0))
        make_data_center(lonlat=(180.0, 90.0))

    def test_longitude_too_low(self):
        with pytest.raises(ValidationError, match="Longitude must be between"):
            make_data_center(lonlat=(-181.0, 0.0))

    def test_longitude_too_high(self):
        with pytest.raises(ValidationError, match="Longitude must be between"):
            make_data_center(lonlat=(181.0, 0.0))

    def test_latitude_too_low(self):
        with pytest.raises(ValidationError, match="Latitude must be between"):
            make_data_center(lonlat=(0.0, -91.0))

    def test_latitude_too_high(self):
        with pytest.raises(ValidationError, match="Latitude must be between"):
            make_data_center(lonlat=(0.0, 91.0))


class TestZoneKeyExists:
    def test_valid_zone_key(self):
        make_data_center(zoneKey=VALID_ZONE_KEY)

    def test_invalid_zone_key(self):
        with pytest.raises(
            ValidationError, match="is not one of the allowed zone keys"
        ):
            make_data_center(zoneKey=INVALID_ZONE_KEY)


class TestDataCentersIdsAreUnique:
    def test_unique_ids_accepted(self):
        DataCenters(
            data_centers=[
                make_data_center(provider="AWS", region="eu-west-1"),
                make_data_center(provider="GCP", region="us-east-1"),
            ]
        )

    def test_duplicate_ids_rejected(self):
        with pytest.raises(ValidationError, match="Duplicate data center ID found"):
            DataCenters(
                data_centers=[
                    make_data_center(provider="AWS", region="eu-west-1"),
                    make_data_center(provider="AWS", region="eu-west-1", zoneKey=FR_ZONE_KEY),
                ]
            )


class TestDataCentersUniqueProviderRegionZoneKey:
    def test_unique_combinations_accepted(self):
        DataCenters(
            data_centers=[
                make_data_center(provider="AWS", region="eu-west-1", zoneKey=VALID_ZONE_KEY),
                make_data_center(provider="GCP", region="us-east-1", zoneKey=FR_ZONE_KEY),
            ]
        )

    def test_duplicate_combination_rejected(self):
        """Duplicate (provider, region, zoneKey) implies duplicate ID (provider-region),
        so the ids_are_unique validator fires first. We verify the entry is rejected."""
        with pytest.raises(ValidationError):
            DataCenters(
                data_centers=[
                    make_data_center(),
                    make_data_center(),
                ]
            )


class TestDataCentersExtraFieldsForbidden:
    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError, match="extra fields not permitted"):
            DataCenters(
                data_centers=[make_data_center()],
                unknown_field="bad",  # type: ignore[call-arg]
            )
