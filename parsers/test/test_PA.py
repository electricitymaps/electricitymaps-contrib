import json
from importlib import resources

import requests
from freezegun import freeze_time
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.PA import fetch_consumption, fetch_exchange, fetch_production


class TestPA(TestCase):
    def setUp(self):
        super().setUp()
        self.adapter = Adapter()
        self.session = requests.Session()
        self.session.mount("https://", self.adapter)

    def test_fetch_production_live(self):
        for frozen_time, mock_json_response in [
            ("2021-12-30 09:58:40", "production_live_20211230.json"),
            ("2024-04-03 02:43:25", "production_live.json"),
        ]:
            with self.subTest(), freeze_time(frozen_time, tz_offset=-5):
                self.adapter.register_uri(
                    GET,
                    ANY,
                    json=json.loads(
                        resources.files("parsers.test.mocks.PA")
                        .joinpath(mock_json_response)
                        .read_text()
                    ),
                    status_code=200,
                )

                production_breakdown_list = fetch_production(session=self.session)

                self.assertMatchSnapshot(
                    [
                        {
                            "datetime": production_breakdown["datetime"].isoformat(),
                            "zoneKey": production_breakdown["zoneKey"],
                            "production": production_breakdown["production"],
                            "storage": production_breakdown["storage"],
                            "source": production_breakdown["source"],
                            "sourceType": production_breakdown["sourceType"].value,
                            "correctedModes": production_breakdown["correctedModes"],
                        }
                        for production_breakdown in production_breakdown_list
                    ]
                )

    @freeze_time("2024-04-03 01:31:45", tz_offset=-5)
    def test_fetch_exchange_live(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.PA")
                .joinpath("exchange_live.json")
                .read_text()
            ),
            status_code=200,
        )

        exchange_list = fetch_exchange(
            ZoneKey("PA"), ZoneKey("CR"), session=self.session
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": exchange["datetime"].isoformat(),
                    "sortedZoneKeys": exchange["sortedZoneKeys"],
                    "netFlow": exchange["netFlow"],
                    "source": exchange["source"],
                    "sourceType": exchange["sourceType"].value,
                }
                for exchange in exchange_list
            ]
        )

    @freeze_time("2024-04-03 01:30:29", tz_offset=-5)
    def test_fetch_consumption(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.PA")
                .joinpath("consumption_live.json")
                .read_text()
            ),
            status_code=200,
        )

        consumption_list = fetch_consumption(session=self.session)

        self.assertMatchSnapshot(
            [
                {
                    "datetime": total_consumption["datetime"].isoformat(),
                    "zoneKey": total_consumption["zoneKey"],
                    "consumption": total_consumption["consumption"],
                    "source": total_consumption["source"],
                    "sourceType": total_consumption["sourceType"].value,
                }
                for total_consumption in consumption_list
            ]
        )
