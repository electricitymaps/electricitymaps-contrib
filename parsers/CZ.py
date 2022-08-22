# based upon https://bitbucket.org/kds_consulting_team/kds-team.ex-ceps/

import json
import logging
import logging.config
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional, Union

import arrow  # the arrow library is used to handle datetimes
import pandas as pd
import pytz
import requests  # the request library is used to fetch content through HTTP
import xmltodict
import zeep
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from zeep.transports import Transport
from zeep.wsdl.utils import etree_to_string

from parsers.lib.config import refetch_frequency

from .lib.exceptions import ParserException

WSDL_URL = "https://www.ceps.cz/_layouts/CepsData.asmx?wsdl"
MAX_RETRIES = 10


class CepsClient:
    def __init__(
        self,
        debug=False,
        max_retries=MAX_RETRIES,
        backoff_factor=0.3,
        session=Session(),
    ):
        self._set_logger(debug)
        # session = Session()
        retry = Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 501, 502, 503, 504),
            allowed_methods=("GET", "POST", "PATCH", "UPDATE"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        transport = Transport(session=session)
        self.client = zeep.Client(WSDL_URL, transport=transport)

    def _set_logger(self, debug):
        if debug:
            log_level = "DEBUG"
        else:
            log_level = "INFO"

        logging.config.dictConfig(
            {
                "version": 1,
                "formatters": {"verbose": {"format": "%(name)s: %(message)s"}},
                "handlers": {
                    "console": {
                        "level": log_level,
                        "class": "logging.StreamHandler",
                        "formatter": "verbose",
                    },
                },
                "loggers": {
                    "zeep.transports": {
                        "level": log_level,
                        "propagate": True,
                        "handlers": ["console"],
                    },
                },
            }
        )

    def get_timeseries_data(
        self,
        endpoint,
        date_start,
        date_end,
        granularity="QH",
        function="AVG",
        version="RT",
        add_para1=True,
    ):
        request_data = {"dateFrom": date_start, "dateTo": date_end}
        if add_para1:
            request_data["para1"] = "all"
        if version:
            request_data["version"] = version
        if function:
            request_data["function"] = function
        if granularity:
            request_data["agregation"] = granularity

        method_to_call = getattr(self.client.service, endpoint)

        try:
            response = method_to_call(**request_data)
        except TypeError as type_error:
            raise CepsClientException(
                f"Invalid request for {endpoint} with request {request_data}. {type_error}"
            ) from type_error
        xml = etree_to_string(response).decode()
        response_data = xmltodict.parse(xml)
        try:
            data = response_data.get("root").get("data").get("item")
            field_names = response_data.get("root").get("series").get("serie")
            add_date = True
            if endpoint == "OfferPrices":
                add_date = False
            data = self.replace_fieldnames(data, field_names, add_date)
            data = self.add_granularity(granularity, data)
            if endpoint == "OdhadovanaCenaOdchylky":
                data = self.add_index(data)
        except AttributeError as att_exc:
            raise CepsClientException(
                f"No data returned for {endpoint} with request {request_data}. "
                f"Try a different aggregation period"
            ) from att_exc

        return data

    def get_data_version(self, endpoint):
        method_to_call = getattr(self.client.service, endpoint)
        response = method_to_call()
        xml = etree_to_string(response).decode()
        response_data = xmltodict.parse(xml)
        return response_data

    def replace_fieldnames(self, data, field_names, add_date):
        field_names_dict = self.process_fieldnames(field_names, add_date)
        for i, datum in enumerate(data):
            for field_name in field_names_dict:
                if field_name in data[i]:
                    data[i][field_names_dict[field_name]] = data[i].pop(field_name)
        return data

    @staticmethod
    def process_fieldnames(field_names, add_date):
        field_names_dict = {}
        if not isinstance(field_names, List):
            field_names = [field_names]
        if add_date:
            field_names_dict["@date"] = "date"
        for field_name in field_names:
            field_names_dict[f"@{field_name['@id']}"] = (
                (field_name["@name"]).lower().replace(" ", "").replace("[mw]", "")
            )
        return field_names_dict

    @staticmethod
    def add_granularity(granularity, data):
        for i, d in enumerate(data):
            data[i]["granularity"] = granularity
        return data

    def add_index(self, data):
        for i, d in enumerate(data):
            data[i]["ordered_index"] = i
        return data


class CepsClientException(Exception):
    pass


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="CZ",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:

    if target_datetime:
        to = arrow.get(target_datetime, "Europe/Prague")
    else:
        to = arrow.now(tz="Europe/Prague")

    # round to previous exact quarter hour to align with API
    minute = 15 * (to.minute // 15)
    to = to.replace(minute=minute)
    to = to.replace(second=0)

    r = session or Session()
    formatted_from = to.shift(days=-1).format("YYYY-MM-DDTHH:mm:ss")
    formatted_to = to.format("YYYY-MM-DDTHH:mm:ss")
    test = CepsClient(session=r)

    production_data = test.get_timeseries_data(
        "Generation", formatted_from, formatted_to
    )
    pumping_data = test.get_timeseries_data(
        "Load", formatted_from, formatted_to, add_para1=False, granularity="MI"
    )
    # Thermal Power Plant - TPP
    # Combined-Cycle Gas Turbine Power Plant - CCGT
    # Nuclear Power Plant - NPP
    # Hydro Power Plant - HPP
    # Pumped-Storage Plant - PsPP
    # Alternative Power Plant - AltPP # assumed biomass?
    # Autoproducer Power Plant - ApPP # deprecated
    # Photovoltaic – PvPP
    # Wind Power Plant – WPP.

    df = pd.DataFrame(production_data)

    # generate datapoints
    hydro_storage = float(
        pumping_data[len(pumping_data) - 1]["loadincludingpumping"]
    ) - float(pumping_data[len(pumping_data) - 1]["load"])
    datapoints = [
        {
            "zoneKey": zone_key,
            "datetime": arrow.get(date).datetime,
            "production": {
                "biomass": float(biomass),
                "coal": float(coal),
                "gas": float(gas),
                "hydro": float(hydro),
                "nuclear": float(nuclear),
                "oil": None,
                "solar": float(solar),
                "wind": float(wind),
                "geothermal": 0.0,
                "unknown": float(other),
            },
            "storage": {
                "hydro": hydro_storage,
            },
            "source": "https://www.ceps.cz/cs/data",
        }
        for date, biomass, coal, gas, hydro, nuclear, solar, wind, other in zip(
            df.date, df.altpp, df.tpp, df.ccgt, df.hpp, df.npp, df.pvpp, df.wpp, df.appp
        )
    ]

    results = datapoints
    return results


def fetch_exchange(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):

    if target_datetime:
        date = arrow.get(target_datetime, "Europe/Prague")
    else:
        date = arrow.now(tz="Europe/Prague")

    # round to previous exact quarter hour to align with API
    minute = 15 * (date.minute // 15)
    date = date.replace(minute=minute)
    date = date.replace(second=0)

    r = session or Session()
    formatted_from = date.shift(minutes=-30).format("YYYY-MM-DDTHH:mm:ss")
    formatted_to = date.shift(minutes=0).format("YYYY-MM-DDTHH:mm:ss")
    test = CepsClient(session=r)

    cross_data = test.get_timeseries_data(
        "CrossborderPowerFlows", formatted_from, formatted_to, add_para1=False
    )
    crossborder = cross_data[len(cross_data) - 1]
    print(crossborder)
    sorted_keys = "->".join(sorted([zone_key1, zone_key2]))

    if "DE" in sorted_keys:
        flow = float(crossborder["tennetactual"]) + float(crossborder["50hztactual"])
        flow = float(flow)
    elif "AT" in sorted_keys:
        flow = (
            float(crossborder["apgactual"]) * -1
        )  # AT is prior to CZ, keep flow direction
    elif "PL" in sorted_keys:
        flow = float(crossborder["psactual"])
    elif "SK" in sorted_keys:
        flow = float(crossborder["sepsactual"])
    else:
        raise NotImplementedError("Unknown zone!")

    return {
        "sortedZoneKeys": sorted_keys,
        "datetime": arrow.get(target_datetime).datetime,
        "netFlow": flow,
        "source": "https://www.ceps.cz/cs/data",
    }


def fetch_exchange_forecast(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):

    if target_datetime:
        date = arrow.get(target_datetime, "Europe/Prague")
    else:
        date = arrow.now(tz="Europe/Prague")

    # round to previous exact quarter hour to align with API
    minute = 15 * (date.minute // 15)
    date = date.replace(minute=minute)
    date = date.replace(second=0)

    r = session or Session()
    formatted_from = date.shift(minutes=-30).format("YYYY-MM-DDTHH:mm:ss")
    formatted_to = date.shift(minutes=0).format("YYYY-MM-DDTHH:mm:ss")
    test = CepsClient(session=r)

    cross_data = test.get_timeseries_data(
        "CrossborderPowerFlows", formatted_from, formatted_to, add_para1=False
    )
    crossborder = cross_data[len(cross_data) - 1]
    print(crossborder)
    sorted_keys = "->".join(sorted([zone_key1, zone_key2]))

    if "DE" in sorted_keys:
        flow = float(crossborder["tennetplanned"]) + float(crossborder["50hztplanned"])
        flow = float(flow)
    elif "AT" in sorted_keys:
        flow = (
            float(crossborder["apgplanned"]) * -1
        )  # AT is prior to CZ, keep flow direction
    elif "PL" in sorted_keys:
        flow = float(crossborder["psplanned"])
    elif "SK" in sorted_keys:
        flow = float(crossborder["sepsplanned"])
    else:
        raise NotImplementedError("Unknown zone!")

    return {
        "sortedZoneKeys": sorted_keys,
        "datetime": arrow.get(target_datetime).datetime,
        "netFlow": flow,
        "source": "https://www.ceps.cz/cs/data",
    }


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key="CZ",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:

    if target_datetime:
        to = arrow.get(target_datetime, "Europe/Prague")
    else:
        to = arrow.now(tz="Europe/Prague")

    r = session or Session()
    formatted_from = to.shift(days=-1).format("YYYY-MM-DDTHH:mm:ss")
    formatted_to = to.format("YYYY-MM-DDTHH:mm:ss")
    test = CepsClient(session=r)

    production_data = test.get_timeseries_data(
        "Load", formatted_from, formatted_to, add_para1=False, granularity="MI"
    )

    return {
        "zoneKey": zone_key,
        "datetime": arrow.get(formatted_to).datetime,
        "consumption": float(production_data[len(production_data) - 1]["load"]),
        "source": "https://www.ceps.cz/cs/data",
    }


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())


# There's a bug in the price end-point
# as per the CEPS notice! To be implemented when this is fixed.
# @refetch_frequency(timedelta(days=1))
# def fetch_price(
#     zone_key: str,
#     session: Optional[Session] = None,
#     target_datetime: Optional[datetime] = None,
#     logger: Logger = getLogger(__name__),
# ) -> list:
#     if target_datetime:
#         now = arrow.get(target_datetime, "Europe/Prague")
#     else:
#         now = arrow.now(tz="Europe/Prague")
