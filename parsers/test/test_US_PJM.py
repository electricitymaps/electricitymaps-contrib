import re
from json import loads
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.US_PJM import fetch_production

base_path_to_mock = Path("parsers/test/mocks/US_PJM")


def test_production(adapter, session, snapshot):
    settings = Path(base_path_to_mock, "settings.json")
    adapter.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    data = Path(base_path_to_mock, "gen_by_fuel.json")
    adapter.register_uri(
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
