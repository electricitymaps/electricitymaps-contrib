import re
from datetime import datetime, timedelta, timezone
from json import loads
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.US_PJM import (
    fetch_consumption_forecast,
    fetch_dayahead_locational_marginal_price,
    fetch_production,
    fetch_realtime_locational_marginal_price,
    fetch_wind_solar_forecasts,
)
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/US_PJM")


def _query_params(requests_mock):
    query = parse_qs(urlparse(requests_mock.last_request.url).query)
    return {key.lower(): value for key, value in query.items()}


def test_production(requests_mock, session, snapshot):
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    data = Path(base_path_to_mock, "gen_by_fuel.json")
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/gen_by_fuel.*"
        ),
        json=loads(data.read_text()),
    )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
    )


def test_fetch_consumption_forecast(requests_mock, session, snapshot):
    # Mock the settings.json request
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    # Mock load forecast request
    data = Path(base_path_to_mock, "compressed_pjm_load_forecast_2025-03-19.gz")
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/load_frcstd_7_day.*"
        ),
        content=data.read_bytes(),  # content for binary data
    )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
    )


def test_fetch_dayahead_locational_marginal_price(requests_mock, session, snapshot):
    # Mock the settings.json request
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    # Mock day-ahead LMP request
    data = Path(base_path_to_mock, "da_hrl_lmps_2026-06-09.json")
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/da_hrl_lmps.*"
        ),
        json=loads(data.read_text()),
    )

    result = fetch_dayahead_locational_marginal_price(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
        target_datetime=datetime(
            2026, 6, 9, 12, 0, tzinfo=ZoneInfo("America/New_York")
        ),
    )
    assert snapshot == result
    assert result[0]["end_datetime"] == result[0]["datetime"] + timedelta(hours=1)

    query_params = _query_params(requests_mock)
    assert query_params["host"] == ["https://api.pjm.com"]
    assert query_params["startrow"] == ["1"]
    assert query_params["rowcount"] == ["1000"]
    assert query_params["type"] == ["ZONE"]
    assert query_params["fields"] == [
        "datetime_beginning_utc,pnode_id,pnode_name,type,total_lmp_da"
    ]
    assert query_params["datetime_beginning_ept"] == [
        "2026-06-09T00:00to2026-06-09T23:59"
    ]


def test_fetch_dayahead_locational_marginal_price_incomplete_response(
    requests_mock, session
):
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    data_path = Path(base_path_to_mock, "da_hrl_lmps_2026-06-09.json")
    data = loads(data_path.read_text())
    data["totalRows"] = len(data["items"]) + 1
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/da_hrl_lmps.*"
        ),
        json=data,
    )

    with pytest.raises(ParserException, match="da_hrl_lmps response incomplete"):
        fetch_dayahead_locational_marginal_price(
            zone_key=ZoneKey("US-MIDA-PJM"),
            session=session,
            target_datetime=datetime(
                2026, 6, 9, 12, 0, tzinfo=ZoneInfo("America/New_York")
            ),
        )


def test_fetch_dayahead_locational_marginal_price_empty_incomplete_response(
    requests_mock, session
):
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/da_hrl_lmps.*"
        ),
        json={"items": [], "totalRows": 1},
    )

    with pytest.raises(ParserException, match="da_hrl_lmps response incomplete"):
        fetch_dayahead_locational_marginal_price(
            zone_key=ZoneKey("US-MIDA-PJM"),
            session=session,
            target_datetime=datetime(
                2026, 6, 9, 12, 0, tzinfo=ZoneInfo("America/New_York")
            ),
        )


def test_fetch_realtime_locational_marginal_price(requests_mock, session, snapshot):
    # Mock the settings.json request
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    # Mock real-time LMP request
    data = Path(base_path_to_mock, "rt_unverified_fivemin_lmps_2026-06-10.json")
    mock_response = loads(data.read_text())
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/rt_unverified_fivemin_lmps.*"
        ),
        json=mock_response,
    )

    result = fetch_realtime_locational_marginal_price(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
        target_datetime=datetime(
            2026, 6, 10, 15, 15, tzinfo=ZoneInfo("America/New_York")
        ),
    )
    assert snapshot == result
    assert result[0]["datetime"] == datetime(2026, 6, 10, 18, 40, tzinfo=timezone.utc)
    assert result[0]["end_datetime"] == result[0]["datetime"] + timedelta(minutes=5)

    query_params = _query_params(requests_mock)
    assert query_params["host"] == ["https://api.pjm.com"]
    assert query_params["startrow"] == ["1"]
    assert query_params["rowcount"] == ["500"]
    assert query_params["pnode_id"] == [
        mock_response["searchSpecification"]["filters"][0]["pnode_id"]
    ]
    assert query_params["fields"] == [
        "datetime_beginning_utc,pnode_id,pnode_name,total_lmp_rt"
    ]
    assert query_params["datetime_beginning_utc"] == [
        "2026-06-10T18:40to2026-06-10T19:15"
    ]


def test_fetch_realtime_locational_marginal_price_incomplete_response(
    requests_mock, session
):
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    data_path = Path(base_path_to_mock, "rt_unverified_fivemin_lmps_2026-06-10.json")
    data = loads(data_path.read_text())
    data["totalRows"] = len(data["items"]) + 1
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/rt_unverified_fivemin_lmps.*"
        ),
        json=data,
    )

    with pytest.raises(
        ParserException, match="rt_unverified_fivemin_lmps response incomplete"
    ):
        fetch_realtime_locational_marginal_price(
            zone_key=ZoneKey("US-MIDA-PJM"),
            session=session,
            target_datetime=datetime(
                2026, 6, 10, 15, 15, tzinfo=ZoneInfo("America/New_York")
            ),
        )


def test_fetch_realtime_locational_marginal_price_empty_incomplete_response(
    requests_mock, session
):
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/rt_unverified_fivemin_lmps.*"
        ),
        json={"items": [], "totalRows": 1},
    )

    with pytest.raises(
        ParserException, match="rt_unverified_fivemin_lmps response incomplete"
    ):
        fetch_realtime_locational_marginal_price(
            zone_key=ZoneKey("US-MIDA-PJM"),
            session=session,
            target_datetime=datetime(
                2026, 6, 10, 15, 15, tzinfo=ZoneInfo("America/New_York")
            ),
        )


def test_fetch_wind_solar_forecasts(requests_mock, session, snapshot):
    # Mock the settings.json request
    settings = Path(base_path_to_mock, "settings.json")
    requests_mock.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    # Mock wind forecast request
    data_wind = Path(base_path_to_mock, "pjm_wind_forecast_2025-02-24.json")
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/hourly_wind_power_forecast.*"
        ),
        json=loads(data_wind.read_text()),
    )

    # Mock solar forecast request
    data_solar = Path(base_path_to_mock, "pjm_solar_forecast_2025-02-24.json")
    requests_mock.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/hourly_solar_power_forecast.*"
        ),
        json=loads(data_solar.read_text()),
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
    )
