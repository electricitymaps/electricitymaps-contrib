import unittest
from datetime import datetime

import arrow
import freezegun
from pytz import timezone
from requests import Session
from requests_mock import ANY, GET, Adapter

from parsers.AR import (
    CAMMESA_DEMANDA_ENDPOINT,
    CAMMESA_EXCHANGE_ENDPOINT,
    CAMMESA_REGIONS_ENDPOINT,
    CAMMESA_RENEWABLES_ENDPOINT,
    CAMMESA_RENEWABLES_REGIONAL_ENDPOINT,
    fetch_exchange,
    fetch_production,
)

REGION_MAPPING = {"national": "1002", "AR-BAS": "425"}
TZ = timezone("America/Argentina/Buenos_Aires")


class ProductionTest(unittest.TestCase):
    """Tests for fetch production at national and regional level."""

    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

        regions_data = open("parsers/test/mocks/AR/RegionesDemanda.json", "rb")

        self.adapter.register_uri(
            GET, CAMMESA_REGIONS_ENDPOINT, content=regions_data.read()
        )
        return super().setUp()

    @freezegun.freeze_time("2023-02-27")
    def test_get_national_production(self):
        national_non_renewable_data = open(
            "parsers/test/mocks/AR/AR_api.cammesa.com.json", "rb"
        )
        self.adapter.register_uri(
            GET,
            f"{CAMMESA_DEMANDA_ENDPOINT}?id_region={REGION_MAPPING['national']}",
            content=national_non_renewable_data.read(),
        )

        national_renewable_data = open(
            "parsers/test/mocks/AR/AR_cdsrenovables.cammesa.com.json", "rb"
        )
        frozen_date = datetime.now(tz=TZ).date().strftime("%d-%m-%Y")
        self.adapter.register_uri(
            GET,
            f"{CAMMESA_RENEWABLES_ENDPOINT}?desde={frozen_date}&hasta={frozen_date}",
            content=national_renewable_data.read(),
        )

        production = fetch_production(session=self.session)
        assert len(production) == 3
        assert (
            production[0]["datetime"]
            == arrow.get(datetime(2023, 2, 27, 1, 25, tzinfo=TZ)).to("UTC").datetime
        )
        assert production[0]["production"]["biomass"] == 124.13
        assert production[0]["production"]["nuclear"] == 1004.2
        assert production[0]["production"]["unknown"] == 9428.5

    @freezegun.freeze_time("2023-03-08 16:47:34", tz_offset=3)
    def test_get_regional_production(self):
        regional_non_renewable_data = open(
            "parsers/test/mocks/AR/AR-BAS_api.cammesa.com.json", "rb"
        )
        self.adapter.register_uri(
            GET,
            f"{CAMMESA_DEMANDA_ENDPOINT}?id_region={REGION_MAPPING['AR-BAS']}",
            content=regional_non_renewable_data.read(),
        )

        regional_renewable_data = open(
            "parsers/test/mocks/AR/AR-BAS_cdsrenovables.cammesa.com.json", "rb"
        )
        self.adapter.register_uri(
            GET,
            CAMMESA_RENEWABLES_REGIONAL_ENDPOINT,
            content=regional_renewable_data.read(),
        )

        production = fetch_production(zone_key="AR-BAS", session=self.session)
        assert len(production) == 1
        assert (
            production[0]["datetime"]
            == arrow.get(datetime(2023, 3, 8, 16, 40, tzinfo=TZ)).to("UTC").datetime
        )
        assert production[0]["production"]["biomass"] == 22
        assert production[0]["production"]["solar"] == 0
        assert production[0]["production"]["wind"] == 1213
        assert production[0]["production"]["hydro"] == 0
        assert production[0]["production"]["nuclear"] == 349.1
        assert production[0]["production"]["unknown"] == 3474.4


class ExchangeTestcase(unittest.TestCase):
    """
    Tests for fetch_exchange.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

        return super().setUp()

    @freezegun.freeze_time("2023-03-08 16:47:34", tz_offset=3)
    def test_get_exchange(self):
        exchange_data = open(
            "parsers/test/mocks/AR/AR-BAS_AR-COM_api.cammesa.com.json", "rb"
        )
        self.adapter.register_uri(
            GET,
            CAMMESA_EXCHANGE_ENDPOINT,
            content=exchange_data.read(),
        )

        exchange = fetch_exchange(
            zone_key1="AR-BAS", zone_key2="AR-COM", session=self.session
        )
        print(exchange)
        assert (
            exchange["datetime"]
            == arrow.get(datetime(2023, 3, 8, 16, 40, tzinfo=TZ)).to("UTC").datetime
        )
        assert exchange["netFlow"] == -3273
