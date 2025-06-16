import logging
import os
from pathlib import Path

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENTSOE
from parsers.ENTSOE import fetch_production

base_path_to_mock = Path("parsers/test/mocks/ENTSOE")


@pytest.fixture(autouse=True)
def entsoe_token_env():
    os.environ["ENTSOE_TOKEN"] = "token"


def test_fetch_consumption(adapter, session, snapshot):
    data = Path(base_path_to_mock, "DK-DK1_consumption.xml")
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_consumption(ZoneKey("DK-DK1"), session)


def test_fetch_consumption_forecast(adapter, session, snapshot):
    data = Path(base_path_to_mock, "DK-DK2_consumption_forecast.xml")
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_consumption_forecast(ZoneKey("DK-DK2"), session)


def test_fetch_generation_forecast(adapter, session, snapshot):
    data = Path(base_path_to_mock, "SE-SE3_generation_forecast.xml")
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_generation_forecast(ZoneKey("SE-SE3"), session)


def test_fetch_prices(adapter, session, snapshot):
    with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
        adapter.register_uri(
            GET,
            ANY,
            content=price_fr_data.read(),
        )

    assert snapshot == ENTSOE.fetch_price(ZoneKey("FR"), session)


def test_fetch_prices_integrated_zone(adapter, session, snapshot):
    with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
        adapter.register_uri(
            GET,
            ANY,
            content=price_fr_data.read(),
        )
    assert snapshot == ENTSOE.fetch_price(ZoneKey("DK-BHM"), session)


def test_fetch_production(adapter, session, snapshot):
    with open(
        "parsers/test/mocks/ENTSOE/FI_production.xml", "rb"
    ) as production_fi_data:
        adapter.register_uri(
            GET,
            ANY,
            content=production_fi_data.read(),
        )
    assert snapshot == ENTSOE.fetch_production(ZoneKey("FI"), session)


def test_fetch_production_with_storage(adapter, session, snapshot):
    with open(
        "parsers/test/mocks/ENTSOE/NO-NO5_production.xml", "rb"
    ) as production_no_data:
        adapter.register_uri(
            GET,
            ANY,
            content=production_no_data.read(),
        )
    assert snapshot == ENTSOE.fetch_production(ZoneKey("NO-NO5"), session)


def test_fetch_with_negative_values(adapter, session, snapshot):
    with open(
        "parsers/test/mocks/ENTSOE/NO-NO5_production-negatives.xml", "rb"
    ) as production_no_data:
        adapter.register_uri(
            GET,
            ANY,
            content=production_no_data.read(),
        )
    logger = logging.Logger("test")
    assert snapshot == ENTSOE.fetch_production(
        ZoneKey("NO-NO5"), session, logger=logger
    )


@pytest.mark.parametrize("zone", ["FI", "LU", "NO-NO5"])
def test_production_with_snapshot(adapter, session, snapshot, zone):
    raw_data = Path(base_path_to_mock, f"{zone}_production.xml")
    adapter.register_uri(
        GET,
        ANY,
        content=raw_data.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_production(ZoneKey(zone), session)


def test_fetch_exchange(adapter, session, snapshot):
    imports = Path(base_path_to_mock, "DK-DK1_GB_exchange_imports.xml")
    exports = Path(base_path_to_mock, "DK-DK1_GB_exchange_exports.xml")

    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10YDK-1--------W&out_Domain=10YGB----------A",
        content=imports.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10YGB----------A&out_Domain=10YDK-1--------W",
        content=exports.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_exchange(
        zone_key1=ZoneKey("DK-DK1"), zone_key2=ZoneKey("GB"), session=session
    )


def test_fetch_exchange_with_aggregated_exchanges(adapter, session, snapshot):
    imports_AC = Path(base_path_to_mock, "FR-COR_IT-SAR_AC_exchange_imports.xml")
    exports_AC = Path(base_path_to_mock, "FR-COR_IT-SAR_AC_exchange_exports.xml")
    imports_DC = Path(base_path_to_mock, "FR-COR_IT-SAR_DC_exchange_imports.xml")
    exports_DC = Path(base_path_to_mock, "FR-COR_IT-SAR_DC_exchange_exports.xml")

    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A885&out_Domain=10Y1001A1001A74G",
        content=imports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A885",
        content=exports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A893&out_Domain=10Y1001A1001A74G",
        content=imports_DC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A893",
        content=exports_DC.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange(
        zone_key1=ZoneKey("FR-COR"),
        zone_key2=ZoneKey("IT-SAR"),
        session=session,
    )


def test_fetch_exchange_forecast(adapter, session, snapshot):
    imports = Path(base_path_to_mock, "DK-DK2_SE-SE4_exchange_forecast_imports.xml")
    exports = Path(base_path_to_mock, "DK-DK2_SE-SE4_exchange_forecast_exports.xml")

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YDK-2--------M&out_Domain=10Y1001A1001A47J",
        content=imports.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A47J&out_Domain=10YDK-2--------M",
        content=exports.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("DK-DK2"),
        zone_key2=ZoneKey("SE-SE4"),
        session=session,
    )


def test_fetch_exchange_forecast_15_min(adapter, session, snapshot):
    imports = Path(base_path_to_mock, "BE_NL_exchange_forecast_imports.xml")
    exports = Path(base_path_to_mock, "BE_NL_exchange_forecast_exports.xml")

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YBE----------2&out_Domain=10YNL----------L",
        content=imports.read_bytes(),
    )

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YNL----------L&out_Domain=10YBE----------2",
        content=exports.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("BE"), zone_key2=ZoneKey("NL"), session=session
    )


def test_fetch_exchange_forecast_with_longer_day_ahead_than_total(
    adapter, session, snapshot
):
    imports = Path(base_path_to_mock, "EE_FI_exchange_forecast_imports.xml")
    exports = Path(base_path_to_mock, "EE_FI_exchange_forecast_exports.xml")

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A39I&out_Domain=10YFI-1--------U",
        content=imports.read_bytes(),
    )

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YFI-1--------U&out_Domain=10Y1001A1001A39I",
        content=exports.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("EE"), zone_key2=ZoneKey("FI"), session=session
    )


def test_fetch_exchange_forecast_with_aggregated_exchanges(adapter, session, snapshot):
    imports_AC = Path(
        base_path_to_mock, "FR-COR_IT-SAR_AC_exchange_forecast_imports.xml"
    )
    exports_AC = Path(
        base_path_to_mock, "FR-COR_IT-SAR_AC_exchange_forecast_exports.xml"
    )
    imports_DC = Path(
        base_path_to_mock, "FR-COR_IT-SAR_DC_exchange_forecast_imports.xml"
    )
    exports_DC = Path(
        base_path_to_mock, "FR-COR_IT-SAR_DC_exchange_forecast_exports.xml"
    )

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A885&out_Domain=10Y1001A1001A74G",
        content=imports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A885",
        content=exports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A893&out_Domain=10Y1001A1001A74G",
        content=imports_DC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A893",
        content=exports_DC.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("FR-COR"),
        zone_key2=ZoneKey("IT-SAR"),
        session=session,
    )


def test_wind_and_solar_forecasts(adapter, session, snapshot):
    day_ahead = Path(base_path_to_mock, "wind_solar_forecast_FI_DAY_AHEAD.xml")
    intraday = Path(base_path_to_mock, "wind_solar_forecast_FI_INTRADAY.xml")
    current = Path(base_path_to_mock, "wind_solar_forecast_FI_CURRENT.xml")

    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A01",
        content=day_ahead.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A40",
        content=intraday.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A18",
        content=current.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_wind_solar_forecasts(ZoneKey("FI"), session)


def test_fetch_uses_normal_url(adapter, session):
    os.environ["ENTSOE_TOKEN"] = "proxy"
    with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
        adapter.register_uri(
            GET,
            ENTSOE.ENTSOE_URL,
            content=price_fr_data.read(),
        )
    ENTSOE.fetch_price(ZoneKey("DE"), session)


def test_refetch_frequency():
    func = fetch_production

    assert func.__name__ == "fetch_production"
