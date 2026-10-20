from pathlib import Path

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.CA_NS import EXCHANGE_URL, fetch_exchange
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

MOCKS = Path(__file__).parent / "mocks" / "CA_NS"


@pytest.mark.parametrize(
    "zone_key1, zone_key2",
    [("CA-NB", "CA-NS"), ("CA-NL", "CA-NS")],
)
def test_fetch_exchange(requests_mock, session, snapshot, zone_key1, zone_key2):
    requests_mock.register_uri(
        GET,
        EXCHANGE_URL,
        content=MOCKS.joinpath("current_report.html").read_bytes(),
    )

    assert snapshot == fetch_exchange(
        ZoneKey(zone_key1), ZoneKey(zone_key2), session=session
    )


def test_fetch_exchange_raises_on_http_error(requests_mock, session):
    requests_mock.register_uri(GET, EXCHANGE_URL, status_code=404, text="")

    with pytest.raises(ParserException, match="404"):
        fetch_exchange(ZoneKey("CA-NL"), ZoneKey("CA-NS"), session=session)
