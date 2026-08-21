from datetime import date
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
    operationalSince: date | None = None,
    operationalUntil: date | None = None,
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
    with (
        patch(
            "electricitymap.contrib.config.data_center_model.ZONES_CONFIG",
            MOCK_ZONES_CONFIG,
            create=True,
        ),
        patch(
            "electricitymap.contrib.config.ZONES_CONFIG",
            MOCK_ZONES_CONFIG,
        ),
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


class TestDateValid:
    @pytest.mark.parametrize("field", ["operationalSince", "operationalUntil"])
    def test_none_accepted(self, field: str):
        dc = make_data_center(**{field: None})  # type: ignore[arg-type]
        assert getattr(dc, field) is None

    @pytest.mark.parametrize("field", ["operationalSince", "operationalUntil"])
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("2021", date(2021, 1, 1)),
            ("2021-06", date(2021, 6, 1)),
            ("2021-06-15", date(2021, 6, 15)),
        ],
    )
    def test_valid_formats_parsed_to_date(self, field: str, value: str, expected: date):
        dc = make_data_center(**{field: value})  # type: ignore[arg-type]
        assert getattr(dc, field) == expected

    @pytest.mark.parametrize("field", ["operationalSince", "operationalUntil"])
    def test_date_object_accepted(self, field: str):
        dc = make_data_center(**{field: date(2021, 6, 15)})  # type: ignore[arg-type]
        assert getattr(dc, field) == date(2021, 6, 15)

    @pytest.mark.parametrize("field", ["operationalSince", "operationalUntil"])
    @pytest.mark.parametrize(
        "value",
        ["not-a-date", "21", "2021/06/15", "2021-6", "2021-06-1", "06-2021"],
    )
    def test_invalid_format_rejected(self, field: str, value: str):
        with pytest.raises(
            ValidationError, match="must be in YYYY, YYYY-MM, or YYYY-MM-DD format"
        ):
            make_data_center(**{field: value})  # type: ignore[arg-type]

    @pytest.mark.parametrize("field", ["operationalSince", "operationalUntil"])
    @pytest.mark.parametrize("value", ["2021-13", "2021-00", "2021-02-30"])
    def test_invalid_calendar_date_rejected(self, field: str, value: str):
        with pytest.raises(ValidationError, match="is not a valid calendar date"):
            make_data_center(**{field: value})  # type: ignore[arg-type]


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
                    make_data_center(
                        provider="AWS", region="eu-west-1", zoneKey=FR_ZONE_KEY
                    ),
                ]
            )


class TestDataCentersUniqueProviderRegionZoneKey:
    def test_unique_combinations_accepted(self):
        DataCenters(
            data_centers=[
                make_data_center(
                    provider="AWS", region="eu-west-1", zoneKey=VALID_ZONE_KEY
                ),
                make_data_center(
                    provider="GCP", region="us-east-1", zoneKey=FR_ZONE_KEY
                ),
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
