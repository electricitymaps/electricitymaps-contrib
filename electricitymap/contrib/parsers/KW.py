"""
This parser returns Kuwait's electricity system load
Source: Ministry of Electricity and Water / State of Kuwait
URL: https://www.mew.gov.kw/en/
Scroll down to see the system load gauge
Shares of Electricity production in 2017: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/statistics/?country=KUWAIT&indicator=ElecGenByFuel)
"""

import re
import ssl
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import requests
import urllib3
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    TotalConsumptionList,
)


# A workaround is required to connect to the API as of 2025-01-14, to avoid the
# following error:
#
#     SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1007)')
#
# The workaround is based on https://stackoverflow.com/a/73519818/2220152.
#
class _CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def _patch_session_for_legacy_connect(session):
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session.mount("https://", _CustomHttpAdapter(ctx))
    return session


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("KW"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    r = _patch_session_for_legacy_connect(session or Session())

    url = "https://www.mew.gov.kw/en"
    response = r.get(url)
    # The regexp gets the load value from a line looking like this:
    #
    # var obj= {"maxValue":10865,"currentValue":7285,"highlights":[{"from":0,"to":10179,"color":"#83e043"},{"from":10179,"to":10604,"color":"#ff6a00"},{"from":10604,"to":10865,"color":"#f12828"}]};
    #
    load = re.findall(r'"currentValue":(\d+)', response.text)
    load = int(load[0])
    consumption = load
    consumption_list = TotalConsumptionList(logger=logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(tz=ZoneInfo("Asia/Kuwait")),
        consumption=consumption,
        source="mew.gov.kw",
    )

    return consumption_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print("fetch_consumption() ->")
    print(fetch_consumption())
