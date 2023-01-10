from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import List, Optional, Union

from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

EXCHANGE_MAPPING = {
    "DE->DK-DK1": {"id": "ExchangeGermany", "direction": 1, "priceArea": "DK1"},
    "DE->DK-DK2": {"id": "ExchangeGermany", "direction": 1, "priceArea": "DK2"},
    "DK-DK1->DK-DK2": {"id": "ExchangeGreatBelt", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->NL": {"id": "ExchangeNetherlands", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->NO-NO2": {"id": "ExchangeNorway", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->SE-SE3": {"id": "ExchangeSweden", "direction": -1, "priceArea": "DK1"},
    "DK-DK2->SE-SE4": {"id": "ExchangeSweden", "direction": -1, "priceArea": "DK2"},
    "DK-BHM->SE-SE4": {"id": "BornholmSE4", "direction": -1, "priceArea": "DK2"},
}


def fetch_data(
    price_area: str,
    session: Optional[Session],
    target_datetime: Optional[datetime],
    logger: Logger,
) -> dict:
    """
    Helper function to fetch data from the API.
    """
    ses = session or Session()

    if target_datetime and target_datetime.tzinfo:
        # Data source doesn't support timezone aware
        # datetimes.
        target_datetime = target_datetime.replace(tzinfo=None)

    params = {
        "limit": 144,
        "filter": '{"PriceArea":"DK1"}'
        if price_area == "DK1"
        else '{"PriceArea":"DK2"}',
        "start": (target_datetime - timedelta(days=1)).isoformat(timespec="minutes")
        if target_datetime
        else None,
        "end": target_datetime.isoformat(timespec="minutes")
        if target_datetime
        else None,
    }
    response: Response = ses.get(
        "https://api.energidataservice.dk/dataset/ElectricityProdex5MinRealtime",
        params=params,
    )
    if response.ok:
        data = response.json()
        if data["total"] == 0:
            raise ParserException(
                parser="DK.py", message=f"No data found for {target_datetime}"
            )
        else:
            return data
    else:
        raise ParserException(parser="DK.py", message="No data was returned")


def flow(sorted_keys: str, datapoint: dict) -> Union[int, float, None]:
    """
    Helper function to extract the net flow from a datapoint.
    """
    if sorted_keys == "DK-DK2->SE-SE4":
        # Exchange from Bornholm to Sweden is included in "ExchangeSweden"
        # but Bornholm island is reported separately from DK-DK2 in Electricity Maps
        return (
            datapoint[EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["id"]]
            * EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["direction"]
            - datapoint[EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["id"]]
            * EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["direction"]
            if datapoint[EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["id"]] is not None
            and datapoint[EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["id"]] is not None
            else None
        )
    else:
        return (
            datapoint[EXCHANGE_MAPPING[sorted_keys]["id"]]
            * EXCHANGE_MAPPING[sorted_keys]["direction"]
            if datapoint[EXCHANGE_MAPPING[sorted_keys]["id"]]
            else None
        )


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str = "DK-DK1",
    zone_key2: str = "DK-DK2",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    sorted_keys = "->".join(sorted([zone_key1, zone_key2]))
    data = fetch_data(
        EXCHANGE_MAPPING[sorted_keys]["priceArea"], session, target_datetime, logger
    )

    if sorted_keys not in EXCHANGE_MAPPING:
        raise ParserException(
            "DK.py",
            "Only able to fetch data for exchanges that are connected to Denmark (DK-DK1, DK-DK2, DK-BHM)",
        )
    else:
        return_list: List[dict] = []
        for datapoint in data["records"]:
            return_list.append(
                {
                    "sortedZoneKeys": sorted_keys,
                    "datetime": datetime.fromisoformat(
                        datapoint["Minutes5UTC"]
                    ).replace(tzinfo=timezone.utc),
                    "netFlow": flow(sorted_keys, datapoint),
                    "source": "energidataservice.dk",
                }
            )
    if return_list == []:
        raise ParserException(
            parser="DK.py",
            message=f"No exchange data found for {sorted_keys} at: {target_datetime or datetime.now()}",
        )
    else:
        return return_list


if __name__ == "__main__":
    print("fetch_exchange(DK-DK2, SE-SE4) ->")
    print(fetch_exchange("DK-DK2", "SE-SE4"))
