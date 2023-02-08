"""
Initial PR https://github.com/electricitymaps/electricitymaps-contrib/pull/2456
Discussion thread https://github.com/electricitymaps/electricitymaps-contrib/issues/636
A promotion webpage for King's Island energy production is here: https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/king-island
As of 09/2020, it embeds with <iframe> the URI https://data.ajenti.com.au/KIREIP/index.html

About the data, the feed we get seems to be counters with a 2 seconds interval.
That means that if we fetch these counters every 15 minutes, we only are reading "instantaneous" metters that could differ from the total quantity of energies at play.
To get the very exact data, we would need to have a parser running constanty to collect those 2-sec interval counters.
"""

import json
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Session
from signalr import Connection

ZONE_PARAMS = {
    "AU-TAS-KI": {
        "hub": "TagHub",
        "method": "Dashboard",
        "tz": "Australia/Currie",
        "source": "https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/king-island",  # Iframe: https://data.ajenti.com.au/KIREIP/index.html
    },
    # Flinders Island
    # https://github.com/electricitymaps/electricitymaps-contrib/issues/2533
    # https://en.wikipedia.org/wiki/Flinders_Island
    "AU-TAS-FI": {
        "hub": "flindershub",
        "method": "SendDashboard",
        "tz": "Australia/Hobart",
        "source": "https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/flinders-island",
    },
    # Rottnest Island
    # https://github.com/electricitymaps/electricitymaps-contrib/issues/2534
    # https://en.wikipedia.org/wiki/Rottnest_Island
    "AU-WA-RI": {
        "hub": "HogsHub",
        "method": "SendDashboard",
        "tz": "Australia/Perth",
        "source": "https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/rottnest-island",
    },
}


class SignalR:
    def __init__(self, url):
        self.url = url

    def update_res(self, msg):
        if msg != {}:
            self.res = msg

    def get_value(self, hub, method):
        self.res = {}
        with Session() as session:
            # create a connection
            connection = Connection(self.url, session)
            chat = connection.register_hub(hub)
            chat.client.on(method, self.update_res)
            connection.start()
            connection.wait(3)
            connection.close()
            return self.res


def parse_payload(logger: Logger, payload) -> dict:
    technologies_parsed = {
        "biomass": 0,
        "battery": 0,
        "coal": 0,
        "flywheel": 0,
        "gas": 0,
        "hydro": 0,
        "nuclear": 0,
        "oil": 0,
        "solar": 0,
        "wind": 0,
        "geothermal": 0,
        "unknown": 0,
    }
    if not "technologies" in payload:
        raise KeyError(
            f"No 'technologies' in payload\n" f"serie : {json.dumps(payload)}"
        )
    else:
        logger.debug(f"serie : {json.dumps(payload)}")
    for technology in payload["technologies"]:
        # rename upstream key to match our payload needs
        if technology["id"] == "diesel":
            technology["id"] = "oil"

        assert technology["unit"] == "kW"
        # The upstream API gives us kW, we need MW
        technologies_parsed[technology["id"]] = int(technology["value"]) / 1000

    # King's Island uses some percentage of biodiesel; since we account differently traditionnal oil & biomass, here we do math to separate both
    if "biodiesel" in payload:
        # sanity check to be sure that we are not remaking data that the data source could otherwise give us
        assert "biomass" and "oil" != 0
        technologies_parsed["biomass"] = (
            technologies_parsed["oil"] * payload["biodiesel"]["percent"] / 100
        )
        technologies_parsed["oil"] = (
            technologies_parsed["oil"] * (100 - payload["biodiesel"]["percent"]) / 100
        )

    logger.debug(f"production : {json.dumps(technologies_parsed)}")

    return technologies_parsed


# Both keys battery and flywheel are negative when storing energy, and positive when feeding energy to the grid
def format_storage_techs(technologies_parsed):
    # sometimes we don't get those keys. For instance Rottnest island don't have any storage.
    if "battery" and "flywheel" in technologies_parsed:
        storage_techs = technologies_parsed["battery"] + technologies_parsed["flywheel"]
    else:
        storage_techs = 0
    battery_production = storage_techs if storage_techs > 0 else 0
    battery_storage = storage_techs if storage_techs < 0 else 0


def sum_storage_techs(technologies_parsed):
    storage_techs = technologies_parsed["battery"] + technologies_parsed["flywheel"]

    return storage_techs


def fetch_production(
    zone_key: str = "AU-TAS-KI",
    session: Optional[Session] = None,
    target_datetime=None,
    logger: Logger = getLogger(__name__),
) -> dict:

    if target_datetime is not None:
        raise NotImplementedError(
            "The datasource currently implemented is only real time"
        )

    # get the specific zone parameters
    try:
        hub, dashboard, tz, source = (
            ZONE_PARAMS[zone_key]["hub"],
            ZONE_PARAMS[zone_key]["method"],
            ZONE_PARAMS[zone_key]["tz"],
            ZONE_PARAMS[zone_key]["source"],
        )
    except KeyError:
        raise KeyError("The zone " + zone_key + " isn't implemented")

    payload = SignalR("https://data.ajenti.com.au/live/signalr").get_value(
        hub, dashboard
    )
    technologies_parsed = parse_payload(logger, payload)
    storage_techs = sum_storage_techs(technologies_parsed)

    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(tz=tz).datetime,
        "production": {
            "biomass": technologies_parsed["biomass"],
            "coal": technologies_parsed["coal"],
            "gas": technologies_parsed["gas"],
            "hydro": technologies_parsed["hydro"],
            "nuclear": technologies_parsed["nuclear"],
            "oil": technologies_parsed["oil"],
            "solar": technologies_parsed["solar"],
            "wind": 0
            if technologies_parsed["wind"] < 0 and technologies_parsed["wind"] > -0.1
            else technologies_parsed[
                "wind"
            ],  # If wind between 0 and -0.1 set to 0 to ignore self-consumption
            "geothermal": technologies_parsed["geothermal"],
            "unknown": technologies_parsed["unknown"],
        },
        "storage": {
            "battery": storage_techs
            * -1  # Somewhat counterintuitively,to ElectricityMap positive means charging and negative means discharging
        },
        "source": source,
    }


if __name__ == "__main__":
    print(fetch_production())
