from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CA_AB import fetch_wind_solar_forecasts

base_path_to_mock = Path("parsers/test/mocks/CA_AB")


def test_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock wind forecast data request
    data_wind = Path(base_path_to_mock, "wind_rpt_longterm.csv")
    adapter.register_uri(
        GET,
        "http://ets.aeso.ca/Market/Reports/Manual/Operations/prodweb_reports/wind_solar_forecast/wind_rpt_longterm.csv",
        text=data_wind.read_text(),
    )

    # Moch solar forecast data request
    data_solar = Path(base_path_to_mock, "solar_rpt_longterm.csv")
    adapter.register_uri(
        GET,
        "http://ets.aeso.ca/Market/Reports/Manual/Operations/prodweb_reports/wind_solar_forecast/solar_rpt_longterm.csv",
        text=data_solar.read_text(),
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("CA-AB"),
        session=session,
    )
