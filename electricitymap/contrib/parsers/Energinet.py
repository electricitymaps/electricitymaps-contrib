from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

ENERGINET_API = "https://api.energidataservice.dk/dataset/GenerationProdTypeExchange"

ZONE_KEY_TO_PRICE_AREA = {
    ZoneKey("DK-DK1"): "DK1",
    ZoneKey("DK-DK2"): "DK2",
}

ENERGINET_TO_PRODUCTION_MIX_MAPPING = {
    "OffshoreWindPower": "wind",
    "OnshoreWindPower": "wind",
    "HydroPower": "hydro",
    "SolarPower": "solar",
    "SolarPowerSelfCon": "solar",
    "Biomass": "biomass",
    "Biogas": "gas",
    "Waste": "biomass",
    "FossilGas": "gas",
    "FossilOil": "oil",
    "FossilHardCoal": "coal",
}


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=ZoneInfo("Europe/Copenhagen"))
    else:
        target_datetime = target_datetime.astimezone(ZoneInfo("Europe/Copenhagen"))

    start_datetime = target_datetime - timedelta(hours=24)
    end_datetime = target_datetime + timedelta(hours=24)

    response = session.get(
        url=ENERGINET_API,
        params={
            "filter": f'{{"PriceArea":"{ZONE_KEY_TO_PRICE_AREA[zone_key]}"}}',
            "start": start_datetime.strftime("%Y-%m-%dT%H:%M"),
            "end": end_datetime.strftime("%Y-%m-%dT%H:%M"),
        },
    )

    obj = response.json()

    records = obj.get("records", [])

    production_list = ProductionBreakdownList(logger=logger)
    for record in records:
        production_mix = ProductionMix()

        for key, value in ENERGINET_TO_PRODUCTION_MIX_MAPPING.items():
            production_mix.add_value(value, record[key])

        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(record["TimeUTC"]).replace(
                tzinfo=ZoneInfo("UTC")
            ),
            production=production_mix,
            source="energinet.dk",
        )

    return production_list.to_list()
