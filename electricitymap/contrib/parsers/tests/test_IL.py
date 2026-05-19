from importlib import resources

import pytest
import requests_mock

from electricitymap.contrib.parsers.IL import IEC_PRODUCTION, fetch_all


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
