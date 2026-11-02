import json
import logging
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from testfixtures import LogCapture

from electricitymap.contrib.parsers import US_ERCOT
from electricitymap.contrib.parsers.lib.exceptions import ParserException


def test_fetch_production():
    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_generation.json") as f:
        fake_generation_data = json.load(f)

    # Since Oct 2026, ERCOT also splits the net "Power Storage" into charging/discharging
    for day in fake_generation_data["data"].values():
        for row in day.values():
            net = row["Power Storage"]["gen"]
            row["Power Storage Charging"] = {"gen": min(net, 0)}
            row["Power Storage Discharging"] = {"gen": max(net, 0)}
            # A key ERCOT might add in the future
            row["Geothermal"] = {"gen": 1}

    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_storage.json") as f:
        fake_storage_data = json.load(f)

    def mock_get_data(url, **kwargs):
        if "energy-storage-resources" in url:
            return fake_storage_data
        else:
            return fake_generation_data

    with patch("electricitymap.contrib.parsers.US_ERCOT.get_data") as gjd:
        gjd.side_effect = mock_get_data
        data = US_ERCOT.fetch_production(logger=logging.getLogger("test"))
    assert data

    assert data[-1]["source"] == "ercot.com"
    assert data[-1]["zoneKey"] == "US-TEX-ERCO"

    # Check that storage data is present and contains battery
    assert isinstance(data[-1]["storage"], dict)
    assert "battery" in data[-1]["storage"]
    assert isinstance(data[-1]["storage"]["battery"], int | float)

    # Verify that there are data points from 2 days (previousDay and currentDay)
    dates = {item["datetime"].date() for item in data}
    assert len(dates) == 2, (
        f"Expected data from exactly 2 days, but got {len(dates)} days: {dates}"
    )


def test_fetch_consumption():
    with open("electricitymap/contrib/parsers/tests/mocks/ERCOT_demand.json") as f:
        fake_data = json.load(f)
    with LogCapture(), patch("electricitymap.contrib.parsers.US_ERCOT.get_data") as gjd:
        gjd.return_value = fake_data
        data = US_ERCOT.fetch_consumption(logger=logging.getLogger("test"))

        assert data
        assert data[0]["consumption"] == 42015.44
        assert data[0]["datetime"] == datetime(
            2024, 11, 24, 0, 0, tzinfo=ZoneInfo("US/Central")
        )
        assert data[0]["source"] == "ercot.com"
        assert data[0]["zoneKey"] == "US-TEX-ERCO"


# Fuel Mix Report columns: local interval-ending times, plus the repeated
# fall-back hour at the end
SLOTS = [f"{end // 60 % 24}:{end % 60:02d}" for end in range(15, 24 * 60 + 15, 15)]
DST_SLOTS = ["01:15 (DST)", "01:30 (DST)", "01:45 (DST)", "02:00 (DST)"]


def _fuel_mix_sheet(days, mwh_by_fuel):
    rows = []
    for day in days:
        for fuel, mwh in mwh_by_fuel.items():
            row = {"Date": pd.Timestamp(day), "Fuel": fuel, **dict.fromkeys(SLOTS, mwh)}
            if day == "2025-11-02":
                row.update(dict.fromkeys(DST_SLOTS, mwh))
            if day == "2025-03-09":
                row.update(dict.fromkeys(["2:15", "2:30", "2:45", "3:00"], None))
            rows.append(row)
    columns = ["Date", "Fuel", "Settlement Type", "Total", *SLOTS, *DST_SLOTS]
    return pd.DataFrame(rows, columns=columns)


class FakeWorkbook:
    def __init__(self, year, mwh_by_fuel):
        self.year, self.mwh_by_fuel = year, mwh_by_fuel

    def parse(self, month):
        days = pd.date_range(f"{month} {self.year}", periods=31, freq="D")
        days = [d.strftime("%Y-%m-%d") for d in days if d.strftime("%b") == month]
        return _fuel_mix_sheet(days, self.mwh_by_fuel(self.year))


def test_parse_fuel_mix_sheet_handles_dst():
    df = US_ERCOT.parse_fuel_mix_sheet(
        _fuel_mix_sheet(["2025-03-09", "2025-11-02"], {"Nuclear": 1000})
    )

    local_days = df.index.tz_convert("US/Central").strftime("%Y-%m-%d")
    assert local_days.value_counts().to_dict() == {"2025-11-02": 100, "2025-03-09": 92}
    assert df.index.is_unique
    assert (df["Nuclear"] == 4000).all()  # MWh per 15 min to MW
    fall_back = df.index[local_days == "2025-11-02"]
    assert (fall_back[1:] - fall_back[:-1] == pd.Timedelta(minutes=15)).all()


def test_fetch_production_maps_other_and_wsl_to_battery_from_2022():
    def mwh_by_fuel(year):
        fuels = {"Gas": 100, "Gas-CC": 50, "Other": 30}
        return fuels | {"WSL": -10} if year >= 2022 else fuels

    with patch.object(
        US_ERCOT,
        "_get_fuel_mix_workbook",
        lambda year, session: FakeWorkbook(year, mwh_by_fuel),
    ):
        data = US_ERCOT.fetch_production(
            target_datetime=datetime(2022, 1, 3, 6, tzinfo=timezone.utc),
            logger=logging.getLogger("test"),
        )
    by_dt = {item["datetime"]: item for item in data}

    # Before 2022, "Other" nets battery and oil: kept as unknown
    before = by_dt[datetime(2021, 12, 31, 18, tzinfo=timezone.utc)]
    assert before["production"]["gas"] == 600
    assert before["production"]["unknown"] == 120
    assert before["storage"] == {}

    # From 2022, "Other" is battery discharge and "WSL" battery charging
    after = by_dt[datetime(2022, 1, 2, 18, tzinfo=timezone.utc)]
    assert after["production"]["gas"] == 600
    assert after["production"].get("unknown") is None
    assert after["storage"]["battery"] == -80  # -(120 - 40), positive is charging


@pytest.mark.parametrize(
    "mwh_by_fuel, error",
    [
        ({}, "ERCOT publishes each month"),  # Month not published yet
        ({"Gas": 100, "Power Storage": 10}, "Unknown fuels"),
    ],
)
def test_fetch_production_raises_on_unusable_fuel_mix_report(mwh_by_fuel, error):
    with (
        patch.object(
            US_ERCOT,
            "_get_fuel_mix_workbook",
            lambda year, session: FakeWorkbook(year, lambda _: mwh_by_fuel),
        ),
        pytest.raises(ParserException, match=error),
    ):
        US_ERCOT.fetch_production(
            target_datetime=datetime(2026, 10, 29, 5, tzinfo=timezone.utc),
            logger=logging.getLogger("test"),
        )


def test_get_fuel_mix_workbook_finds_yearly_report_or_archive():
    def xlsx(sheet):
        content = BytesIO()
        pd.DataFrame({"Date": []}).to_excel(content, sheet_name=sheet)
        return content.getvalue()

    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("IntGenbyFuel2023.xlsx", xlsx("2023"))
    page = """
        <a href="https://www.ercot.com/files/docs/2026/02/09/IntGenbyFuel2026.xlsx">
          <span>Fuel Mix Report: 2026</span></a>
        <a href="https://www.ercot.com/files/docs/2021/03/10/FuelMixReport_PreviousYears.zip">
          Fuel Mix Report: 2007 - 2024</a>
    """
    files = {
        US_ERCOT.GENERATION_PAGE_URL: page.encode(),
        "https://www.ercot.com/files/docs/2026/02/09/IntGenbyFuel2026.xlsx": xlsx(
            "2026"
        ),
        "https://www.ercot.com/files/docs/2021/03/10/FuelMixReport_PreviousYears.zip": archive.getvalue(),
    }

    US_ERCOT._get_fuel_mix_archive.cache_clear()
    with patch.object(US_ERCOT, "_get_ercot_file", lambda url, session: files[url]):
        assert US_ERCOT._get_fuel_mix_workbook(2026, None).sheet_names == ["2026"]
        assert US_ERCOT._get_fuel_mix_workbook(2023, None).sheet_names == ["2023"]
        with pytest.raises(ParserException, match="No Fuel Mix Report found for 2030"):
            US_ERCOT._get_fuel_mix_workbook(2030, None)
    US_ERCOT._get_fuel_mix_archive.cache_clear()
