import unittest
from datetime import datetime

import arrow
import freezegun
from pytz import timezone
from requests import Session
from requests_mock import ANY, GET, Adapter

from parsers.AR import (
    CAMMESA_DEMANDA_ENDPOINT,
    CAMMESA_REGIONS_ENDPOINT,
    CAMMESA_RENEWABLES_ENDPOINT,
    CAMMESA_RENEWABLES_REGIONAL_ENDPOINT,
    fetch_production,
)

REGION_MAPPING = {"national": "1002"}
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
            "parsers/test/mocks/AR/api.cammesa.com.json", "rb"
        )
        self.adapter.register_uri(
            GET,
            f"{CAMMESA_DEMANDA_ENDPOINT}?id_region={REGION_MAPPING['national']}",
            content=national_non_renewable_data.read(),
        )

        national_renewable_data = open(
            "parsers/test/mocks/AR/cdsrenovables.cammesa.com.json", "rb"
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
