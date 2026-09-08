from datetime import datetime, timedelta
from logging import getLogger

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.types import ZoneKey

from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

DOMAIN_MAPPING = {
    "FR-COR": "https://opendata-corse.edf.fr",
    "RE": "https://opendata-reunion.edf.fr",
    "GF": "https://opendata-guyane.edf.fr",
    "MQ": "https://opendata-martinique.edf.fr",
    "GP": "https://opendata-guadeloupe.edf.fr",
}

LIVE_DATASETS = {
    "FR-COR": "production-delectricite-par-filiere-en-temps-reel",
    "GP": "mix-temps-reel-guadeloupe",
    "RE": "prod-electricite-temps-reel",
    "GF": "production-d-electricite-par-filiere-en-temps-reel",
    "MQ": "production-delectricite-par-filiere-en-temps-reel",
}

HISTORICAL_MAPPING = {
    "FR-COR": "Corse",
    "RE": "Réunion",
    "GF": "Guyane",
    "MQ": "Martinique",
    "GP": "Guadeloupe",
}

API_PARAMETER_GROUPS = {
    "production": {
        "RE": {
            "bioenergies": "biomass",
            "charbon": "biomass",
            "diesel": "biomass",
            "eolien": "wind",
            "hydraulique": "hydro",
            "photovoltaique": "solar",
            "turbines_combustion": "gas",
        },
        "GP": {
            "charbon": "coal",
            "bioenergies": "biomass",
            "diesel": "oil",
            "hydraulique": "hydro",
            "photovoltaique": "solar",
            "eolien": "wind",
            "turbines_combustion": "gas",
            "geothermie": "geothermal",
        },
        "GF": {
            "bioenergies": "biomass",
            "hydraulique": "hydro",
            "moteur_diesel": "oil",
            "photovoltaique": "solar",
            "tac": "oil",
        },
        "MQ": {
            "bioenergies": "biomass",
            "eolien": "wind",
            "hydraulique": "hydro",
            "moteurs_diesels": "oil",
            "photovoltaique": "solar",
            "turbines_combustion": "gas",
        },
        "FR-COR": {
            "moteur_diesel": "oil",
            "tac": "gas",
            "hydraulique": "hydro",
            "micro_hydro": "hydro",
            "photovoltaique": "solar",
            "eolien": "wind",
            "bioenergies": "biomass",
        },
    },
    "storage": {"battery": ["solde_stockage", "stockage"]},
    "price": {
        "price": ["cout_moyen_de_production_eur_mwh"],
    },
}

STORAGE_MAPPING = {
    API_TYPE: data_type
    for key in ["storage"]
    for data_type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

PRICE_MAPPING = {
    API_TYPE: data_type
    for key in ["price"]
    for data_type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

IGNORED_VALUES = [
    "jour",
    "total",
    "statut",
    "date",
    "date_jour",
    "heure",
    "liaisons",
    "tac",
]

# The API exposes aggregate sub-totals (``filiere_*``) and percentage shares
# (``part_*``) alongside the per-mode generation values. These must be ignored
# to avoid double counting.
IGNORED_PREFIXES = ("part_", "filiere_")

# Historical data is served by a different, national dataset
# (``courbe-de-charge-de-la-production-delectricite-par-filiere``) which uses a
# more aggregated schema (``*_mw`` suffixes) than the per-territory live feeds.
# Thermal generation (oil/gas) and bagasse/coal are each reported as a single
# lumped value that cannot be split into individual modes, so both are reported
# as ``unknown``.
HISTORICAL_GENERATION_MAPPING = {
    "photovoltaique_mw": "solar",
    "eolien_mw": "wind",
    "hydraulique_mw": "hydro",
    "micro_hydraulique_mw": "hydro",
    "bioenergies_mw": "biomass",
    "geothermie_mw": "geothermal",
    "thermique_mw": "unknown",
    "bagasse_charbon_mw": "unknown",
}

HISTORICAL_STORAGE_MAPPING = {"stockage_mw": "battery"}

HISTORICAL_IGNORED_VALUES = [
    "date_heure",
    "territoire",
    "statut",
    "production_totale_mw",
    "importations_mw",
    "cout_moyen_de_production_eur_mwh",
]


def generate_url(zone_key, target_datetime):
    if target_datetime:
        return "https://opendata.edf.fr/api/explore/v2.1/catalog/datasets/courbe-de-charge-de-la-production-delectricite-par-filiere/exports/json"
    return f"{DOMAIN_MAPPING[zone_key]}/api/explore/v2.1/catalog/datasets/{LIVE_DATASETS[zone_key]}/exports/json"


def fetch_data(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
) -> tuple[list, str, str]:
    ses = session or Session()

    if target_datetime is None and zone_key not in LIVE_DATASETS:
        raise ParserException(
            "FR_O.py",
            f"Live data not implemented for {zone_key} in this parser.",
            zone_key,
        )

    target_date = target_datetime.strftime("%Y-%m-%d") if target_datetime else None
    past_date = (
        (target_datetime - timedelta(days=3)).strftime("%Y-%m-%d")
        if target_datetime
        else None
    )

    URL_QUERIES: dict[str, str | None] = (
        {
            "timezone": "UTC",
            "order_by": "date_heure",
            "where": f"date_heure >= date'{past_date}' AND date_heure <= date'{target_date}'",
            "refine": f"territoire:{HISTORICAL_MAPPING[zone_key]}",
        }
        if target_datetime
        else {
            "timezone": "UTC",
            "order_by": "date",
        }
    )

    url = generate_url(zone_key, target_datetime)
    response: Response = ses.get(url, params=URL_QUERIES)
    data: dict | list | None = response.json()
    if data == []:
        raise ParserException(
            "FR_O.py",
            f"No data available for {zone_key} for {target_datetime.strftime('%Y')}"
            if target_datetime
            else f"No live data available for {zone_key}.",
            zone_key,
        )
    elif isinstance(data, dict):
        if data.get("errorcode") == "10002":
            raise ParserException(
                "FR_O.py",
                f"Rate limit exceeded. Please try again later after: {data.get('reset_time')}",
            )
        elif data.get("error_code") == "ODSQLError":
            raise ParserException(
                "FR_O.py",
                "Query malformed. Please check the parameters. If this was previously working there has likely been a change in the API.",
            )
    if not isinstance(data, list):
        raise ParserException(
            "FR_O.py",
            f"Unexpected data format for {zone_key} for {target_datetime}"
            if target_datetime
            else f"Unexpected data format for {zone_key}.",
            zone_key,
        )
    source = url.split("//")[1].split("/")[0]
    return data, "date_heure" if target_datetime else "date", source


@refetch_frequency(timedelta(hours=72))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger=getLogger(__name__),
):
    production_objects, date_string, source = fetch_data(
        zone_key, session, target_datetime
    )

    # Historical and live data come from different datasets with different
    # schemas, so the mappings used to interpret each field differ accordingly.
    is_historical = target_datetime is not None
    generation_mapping = (
        HISTORICAL_GENERATION_MAPPING
        if is_historical
        else API_PARAMETER_GROUPS["production"][zone_key]
    )
    storage_mapping = HISTORICAL_STORAGE_MAPPING if is_historical else STORAGE_MAPPING
    ignored_values = HISTORICAL_IGNORED_VALUES if is_historical else IGNORED_VALUES
    ignored_prefixes = () if is_historical else IGNORED_PREFIXES

    production_breakdown_list = ProductionBreakdownList(logger=logger)
    for production_object in production_objects:
        production = ProductionMix()
        storage = StorageMix()
        for mode_key in production_object:
            if mode_key in generation_mapping:
                production.add_value(
                    generation_mapping[mode_key],
                    production_object[mode_key],
                    correct_negative_with_zero=True,
                )
            elif mode_key in storage_mapping:
                value = production_object[mode_key]
                storage.add_value(
                    storage_mapping[mode_key],
                    -value if value is not None else None,
                )
            elif mode_key in ignored_values or mode_key.startswith(ignored_prefixes):
                pass
            else:
                logger.warning(
                    f"Unknown mode_key: '{mode_key}' encountered for {zone_key}."
                )

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(production_object[date_string]),
            production=production,
            storage=storage,
            source=source,
            sourceType=EventSourceType.estimated
            if production_object.get("statut") == "Estimé"
            else EventSourceType.measured,
        )
    return production_breakdown_list.to_list()


@refetch_frequency(timedelta(hours=72))
def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger=getLogger(__name__),
):
    data_objects, date_string, source = fetch_data(zone_key, session, target_datetime)

    price_list = PriceList(logger=logger)
    for data_object in data_objects:
        price: float | int | None = None
        for mode_key in data_object:
            if mode_key in PRICE_MAPPING:
                price = data_object[mode_key]
                break
        if price is not None:
            price_list.append(
                zoneKey=zone_key,
                currency="EUR",
                datetime=datetime.fromisoformat(data_object[date_string]),
                source=source,
                price=price,
            )
    return price_list.to_list()
