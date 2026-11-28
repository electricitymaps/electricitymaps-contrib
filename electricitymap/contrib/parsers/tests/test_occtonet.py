"""Tests for the OCCTO interconnection parser (Japanese exchanges)."""

from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import occtonet
from electricitymap.contrib.types import ZoneKey

MOCKS = Path("electricitymap/contrib/parsers/tests/mocks/occtonet")
LOGIN_URL = "http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login"
DATA_URL = "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C"
TARGET = datetime(2026, 11, 24, 12, tzinfo=ZoneInfo("Asia/Tokyo"))
# The mocks were recorded on 2026-11-25 (JST) for 2026-11-24.
NOW = "2026-11-25 03:00:00"


def mock_occtonet(requests_mock, csv_per_line: dict[str, bytes]) -> None:
    """Answers the three POSTs OCCTO needs per line: header, token, then the CSV download."""
    requests_mock.get(LOGIN_URL, text="")

    def answer(request, context):
        form = {k: v[0] for k, v in parse_qs(request.body).items()}
        step = form["fwExtention.actionSubType"]
        if step == "headerInput":
            return (MOCKS / "header_input.json").read_bytes()
        if step == "ok":
            return (MOCKS / "ok.json").read_bytes()
        return csv_per_line[form["tgtRkl"]]

    requests_mock.post(DATA_URL, content=answer)


def read_line(name: str) -> bytes:
    return (MOCKS / name).read_bytes()


def drop_rows(csv: bytes, times: list[str]) -> bytes:
    """The same CSV without the rows at the given times (e.g. "12:00")."""
    lines = csv.decode("shift-jis").splitlines(keepends=True)
    kept = [line for line in lines if not any(f",{t}," in line for t in times)]
    return "".join(kept).encode("shift-jis")


@freeze_time(NOW)
def test_snapshot_fetch_exchange(requests_mock, session, snapshot):
    # Line 05 published nothing that day, so JP-CB->JP-HR is line 11 alone.
    mock_occtonet(
        requests_mock,
        {
            "05": read_line("line_05_20261124.csv"),
            "11": read_line("line_11_20261124.csv"),
        },
    )
    assert snapshot == occtonet.fetch_exchange(
        ZoneKey("JP-HR"), ZoneKey("JP-CB"), session, TARGET
    )


@freeze_time(NOW)
def test_fetch_exchange_reads_measured_flow(requests_mock, session):
    mock_occtonet(
        requests_mock,
        {
            "05": read_line("line_05_20261124.csv"),
            "11": read_line("line_11_20261124.csv"),
        },
    )
    exchanges = occtonet.fetch_exchange(
        ZoneKey("JP-CB"), ZoneKey("JP-HR"), session, TARGET
    )

    assert len(exchanges) == 288  # every 5 minutes
    first, last = exchanges[0], exchanges[-1]
    assert first["datetime"] == datetime(
        2026, 11, 24, 0, 5, tzinfo=ZoneInfo("Asia/Tokyo")
    )
    assert first["netFlow"] == -607  # 潮流実績 (measured flow)
    assert first["sortedZoneKeys"] == "JP-CB->JP-HR"
    assert first["source"] == "occtonet.occto.or.jp"
    assert first["sourceType"] == EventSourceType.measured
    # "24:00" is midnight of the next day.
    assert last["datetime"] == datetime(
        2026, 11, 25, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")
    )


@freeze_time(NOW)
def test_fetch_exchange_forecast_reads_planned_flow(requests_mock, session):
    mock_occtonet(
        requests_mock,
        {
            "05": read_line("line_05_20261124.csv"),
            "11": read_line("line_11_20261124.csv"),
        },
    )
    forecasts = occtonet.fetch_exchange_forecast(
        ZoneKey("JP-CB"), ZoneKey("JP-HR"), session, TARGET
    )

    assert len(forecasts) == 288
    # 計画潮流(順方向) (planned flow), not the measured -607 of the same timestamp.
    assert forecasts[0]["netFlow"] == -637
    assert all(f["sourceType"] == EventSourceType.forecasted for f in forecasts)


@freeze_time(NOW)
def test_flows_of_several_lines_are_summed(requests_mock, session):
    line = read_line("line_11_20261124.csv")
    # The second line misses 12:00: that timestamp has no complete sum and is left out.
    mock_occtonet(requests_mock, {"05": drop_rows(line, ["12:00"]), "11": line})
    exchanges = occtonet.fetch_exchange(
        ZoneKey("JP-CB"), ZoneKey("JP-HR"), session, TARGET
    )

    assert len(exchanges) == 287
    assert exchanges[0]["netFlow"] == 2 * -607
    noon = datetime(2026, 11, 24, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
    assert noon not in {e["datetime"] for e in exchanges}


@freeze_time(NOW)
def test_flow_direction_is_reverted(requests_mock, session):
    # JP-CB->JP-TK (line 03) is published in the opposite direction.
    mock_occtonet(requests_mock, {"03": read_line("line_11_20261124.csv")})
    exchanges = occtonet.fetch_exchange(
        ZoneKey("JP-CB"), ZoneKey("JP-TK"), session, TARGET
    )

    assert exchanges[0]["netFlow"] == 607


@freeze_time(NOW)
def test_empty_day_returns_no_exchange(requests_mock, session):
    mock_occtonet(requests_mock, {"04": read_line("line_05_20261124.csv")})
    assert (
        occtonet.fetch_exchange(ZoneKey("JP-CB"), ZoneKey("JP-KN"), session, TARGET)
        == []
    )


@freeze_time(NOW)
def test_fetch_exchange_forecast_refuses_future_days(session):
    with pytest.raises(NotImplementedError):
        occtonet.fetch_exchange_forecast(
            ZoneKey("JP-CB"),
            ZoneKey("JP-HR"),
            session,
            datetime(2026, 11, 27, tzinfo=ZoneInfo("Asia/Tokyo")),
        )
