import json
from datetime import datetime, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers.GB import (
    ELEXON_BMU_FUEL_TYPE_URL,
    ELEXON_BMU_UNITS,
    ELEXON_BOALF_STREAM,
    ELEXON_MELS_STREAM,
    ELEXON_MILS_STREAM,
    ELEXON_PN_STREAM,
    NESO_API,
    fetch_price,
    fetch_production,
    fetch_wind_forecasts_day_ahead,
)
from electricitymap.contrib.types import ZoneKey


@pytest.mark.parametrize(
    "zone_key", ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]
)
@freeze_time("2024-04-14 15:10:57")
def test_fetch_price_live(requests_mock, session, snapshot, zone_key):
    requests_mock.register_uri(
        GET,
        ANY,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks.GB")
        .joinpath("eco2mix_api_live.xml")
        .read_text(),
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_price(
        zone_key=ZoneKey(zone_key), session=session
    )


def test_fetch_price_historical(requests_mock, session, snapshot):
    requests_mock.register_uri(
        GET,
        ANY,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks.GB")
        .joinpath("eco2mix_api_historical_20220716.xml")
        .read_text(),
    )

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    assert snapshot == fetch_price(target_datetime=historical_datetime, session=session)


@freeze_time("2024-12-16 12:00:00")
def test_fetch_production(requests_mock, session, snapshot):
    neso_mock = resources.files("electricitymap.contrib.parsers.tests.mocks.GB")
    gb_mock = resources.files("electricitymap.contrib.parsers.tests.mocks.GB")

    requests_mock.register_uri(
        GET,
        "https://api.neso.energy/api/3/action/datastore_search_sql",
        json=json.loads(neso_mock.joinpath("production.json").read_text()),
    )
    requests_mock.register_uri(
        GET,
        ELEXON_BMU_UNITS,
        json=json.loads(gb_mock.joinpath("bmunits.json").read_text()),
    )
    bmvalues = json.loads(gb_mock.joinpath("bmvalues.json").read_text())
    requests_mock.register_uri(GET, ELEXON_PN_STREAM, json=bmvalues)
    requests_mock.register_uri(GET, ELEXON_MELS_STREAM, json=bmvalues)
    requests_mock.register_uri(GET, ELEXON_MILS_STREAM, json=bmvalues)
    requests_mock.register_uri(
        GET,
        ELEXON_BOALF_STREAM,
        json=json.loads(gb_mock.joinpath("boalf.json").read_text()),
    )
    requests_mock.register_uri(
        GET,
        ELEXON_BMU_FUEL_TYPE_URL,
        content=gb_mock.joinpath("bmu_fuel_type.xlsx").read_bytes(),
    )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("GB"),
        session=session,
    )


@freeze_time("2024-12-16 12:00:00")
def test_fetch_wind_solar_forecasts_day_ahead_live(requests_mock, session, snapshot):
    gb_mock = resources.files("electricitymap.contrib.parsers.tests.mocks.GB")
    requests_mock.register_uri(
        GET,
        NESO_API,
        json=json.loads(
            gb_mock.joinpath("wind_day_ahead_forecast_live.json").read_text()
        ),
    )

    assert snapshot == fetch_wind_forecasts_day_ahead(
        zone_key=ZoneKey("GB"),
        session=session,
    )


def test_fetch_wind_forecasts_day_ahead_historical(requests_mock, session, snapshot):
    gb_mock = resources.files("electricitymap.contrib.parsers.tests.mocks.GB")
    requests_mock.register_uri(
        GET,
        NESO_API,
        json=json.loads(
            gb_mock.joinpath("wind_day_ahead_forecast_historical.json").read_text()
        ),
    )

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    assert snapshot == fetch_wind_forecasts_day_ahead(
        zone_key=ZoneKey("GB"),
        session=session,
        target_datetime=historical_datetime,
    )
