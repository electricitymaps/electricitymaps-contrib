import time
import datetime
import logging
from pathlib import Path
import json
import importlib
import pytest

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()
ZONES_CONFIG = json.load(open(CONFIG_DIR.joinpath("zones.json")))
EXCHANGES_CONFIG = json.load(open(CONFIG_DIR.joinpath("exchanges.json")))


# Prepare all parsers
CONSUMPTION_PARSERS = {}
PRODUCTION_PARSERS = {}
PRODUCTION_PER_MODE_FORECAST_PARSERS = {}
PRODUCTION_PER_UNIT_PARSERS = {}
EXCHANGE_PARSERS = {}
PRICE_PARSERS = {}
CONSUMPTION_FORECAST_PARSERS = {}
GENERATION_FORECAST_PARSERS = {}
EXCHANGE_FORECAST_PARSERS = {}

PARSER_KEY_TO_DICT = {
    "consumption": CONSUMPTION_PARSERS,
    "production": PRODUCTION_PARSERS,
    "productionPerUnit": PRODUCTION_PER_UNIT_PARSERS,
    "productionPerModeForecast": PRODUCTION_PER_MODE_FORECAST_PARSERS,
    "exchange": EXCHANGE_PARSERS,
    "price": PRICE_PARSERS,
    "consumptionForecast": CONSUMPTION_FORECAST_PARSERS,
    "generationForecast": GENERATION_FORECAST_PARSERS,
    "exchangeForecast": EXCHANGE_FORECAST_PARSERS,
}

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s"
)


# Read all zones
for zone_id, zone_config in ZONES_CONFIG.items():
    for parser_key, v in zone_config.get("parsers", {}).items():
        mod_name, fun_name = v.split(".")
        mod = importlib.import_module("parsers.%s" % mod_name)
        PARSER_KEY_TO_DICT[parser_key][zone_id] = getattr(mod, fun_name)

# Read all exchanges
for exchange_id, exchange_config in EXCHANGES_CONFIG.items():
    for parser_key, v in exchange_config.get("parsers", {}).items():
        mod_name, fun_name = v.split(".")
        mod = importlib.import_module("parsers.%s" % mod_name)
        PARSER_KEY_TO_DICT[parser_key][exchange_id] = getattr(mod, fun_name)


zones = ["DK-DK1", "DE", "HR"]


@pytest.mark.parametrize("zone", zones)
def test_parser_outputs(zone, snapshot):
    if ZONES_CONFIG[zone].get("parsers", {}).get("production"):
        res = _test_parser(zone, data_type="production")
        snapshot.assert_match(res)


exchanges = ["BR-CS->BR-N", "CA-MB->US-MIDW-MISO", "RU-1->RU-2"]


@pytest.mark.parametrize("zone", exchanges)
def test_parser_outputs_exchange(zone, snapshot):
    res = _test_parser(zone, data_type="exchange")
    snapshot.assert_match(res)


def _test_parser(zone, data_type):
    target_datetime = None

    print(f"test {zone} {data_type}")
    parser = PARSER_KEY_TO_DICT[data_type][zone]
    if data_type in ["exchange", "exchangeForecast"]:
        args = zone.split("->")
    else:
        args = [zone]
    res = parser(
        *args, target_datetime=target_datetime, logger=logging.getLogger(__name__)
    )

    if data_type == "production":
        return res[-1]

    if not res:
        return {}
        # raise ValueError(f"Error: {zone} parser returned nothing".format(res))

    if isinstance(res, (list, tuple)):
        res_list = list(res)
    else:
        res_list = [res]

    try:
        dts = [e["datetime"] for e in res_list]
    except:
        raise ValueError(
            "Parser output lacks `datetime` key for at least some of the "
            "ouput. Full ouput: \n\n{}\n".format(res)
        )

    assert all(
        [type(e["datetime"]) is datetime.datetime for e in res_list]
    ), "Datetimes must be returned as native datetime.datetime objects"

    return res
