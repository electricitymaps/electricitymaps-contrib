from importlib import resources

import pytest
import requests_mock
from requests import Session

from electricitymap.contrib.parsers.IL import (
    IEC_PRODUCTION,
    URL,
    fetch_all,
    fetch_production,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException


def test_snapshot_fetch_all(snapshot):
    """Snapshot the full fetch_all output. Exercises BeautifulSoup(lxml)
    parsing of the IEC dashboard. `fetch_all` calls module-level `requests.get`
    twice, so we patch the global requests_mock via `requests_mock.Mocker`.
    """
    html = (
        resources.files("electricitymap.contrib.parsers.tests.mocks.IL")
        .joinpath("iec_dashboard.html")
        .read_bytes()
    )

    with requests_mock.Mocker() as m:
        m.get(IEC_PRODUCTION, content=html)
        values = fetch_all()

    assert snapshot == values


def test_fetch_all_raises_when_no_status_spans():
    """If lxml parses a dashboard without any statusVal spans, the parser
    should raise a clear ValueError rather than returning an empty result."""
    with requests_mock.Mocker() as m:
        m.get(IEC_PRODUCTION, text="<html><body>no spans here</body></html>")
        with pytest.raises(ValueError, match="Could not parse IEC dashboard"):
            fetch_all()


def test_fetch_production_raises_on_http_error():
    """A failed Noga-ISO request should raise with the status code instead of
    trying to decode the error page as JSON."""
    session = Session()
    with requests_mock.Mocker(session=session) as m:
        m.get(URL, status_code=503, text="<html>Service Unavailable</html>")
        with pytest.raises(ParserException, match="503"):
            fetch_production(session=session)
