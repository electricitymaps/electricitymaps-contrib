import unittest
from datetime import datetime

from pytz import timezone
from requests import Session
from requests_mock import ANY, Adapter

from parsers import NTESMO

australia = timezone("Australia/Darwin")


class TestNTESMO(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        data = open("parsers/test/mocks/AU/NTESMO.xlsx", "rb")
        self.adapter.register_uri(ANY, ANY, content=data.read())
        index_page = """<div class="smp-tiles-article__item">
                <a href="https://ntesmo.com.au/__data/assets/excel_doc/0013/116113/Market-Information_System-Control-daily-trading-day_220401.xlsx">
                    <div class="smp-tiles-article__title">01 December 2022</div>

                    <div class="smp-tiles-article__lower d-flex flex-nowrap justify-content-between align-content-center align-items-center">
                        <div class="col-9 no-padding">
                            <strong>Download</strong>
                            <span>MS Excel Document (115.5 KB)</span>
                        </div>
                        <div class="col-3 no-padding d-flex justify-content-end">
                            <svg xmlns="http://www.w3.org/2000/svg" width="33" height="34" viewBox="0 0 33 34">
                                <path fill="currentColor" d="M-1223.7-1933.8h.2l.6.6.6-.6h.2v-.2l8.6-8.5-1.2-1.2-7.4 7.5v-22.6h-1.6v22.6l-7.4-7.5-1.2 1.2 8.6 8.5z" transform="translate(1239 1959)"></path>
                                <path fill="currentColor" class="st0" d="M-1207.8-1938.1v11.3h-29.4v-11.3h-1.6v12.9h32.6v-12.9z" transform="translate(1239 1959)"></path>
                            </svg>
                        </div>
                    </div>
                </a>
            </div>"""
        self.adapter.register_uri(ANY, NTESMO.INDEX_URL.format(2022), text=index_page)

    def test_fetch_production(self):
        data_list = NTESMO.fetch_production_mix(
            "AU-NT", self.session, target_datetime=datetime(year=2022, month=12, day=1)
        )[:2]
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "production": {"gas": 96, "biomass": 13, "unknown": 0},
                "storage": {},
            },
            {
                "production": {"gas": 96, "biomass": 13, "unknown": 0},
                "storage": {},
            },
        ]
        self.assertEqual(len(data_list), len(expected_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(actual["zoneKey"], "AU-NT")
            self.assertEqual(actual["source"], "ntesmo.com.au")
            for production_type, production in actual["production"].items():
                self.assertEqual(
                    production, expected_data[index]["production"][production_type]
                )

    def test_fetch_price(self):
        data_list = NTESMO.fetch_price(
            "AU-NT", self.session, target_datetime=datetime(year=2022, month=12, day=1)
        )
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "price": 500,
                "currency": "AUD",
            }
        ] * 48
        self.assertEqual(len(data_list), len(expected_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(actual["zoneKey"], "AU-NT")
            self.assertEqual(actual["source"], "ntesmo.com.au")
            self.assertEqual(actual["price"], expected_data[index]["price"])
            self.assertEqual(actual["currency"], expected_data[index]["currency"])

        # Check that the dates corresponds to two days:

        self.assertEqual(
            data_list[0]["datetime"],
            australia.localize(
                (datetime(year=2022, month=12, day=1, hour=4, minute=30))
            ),
        )
        self.assertEqual(
            data_list[-1]["datetime"],
            australia.localize(datetime(year=2022, month=12, day=2, hour=4, minute=00)),
        )

    def test_fetch_consumption(self):
        data_list = NTESMO.fetch_consumption(
            "AU-NT", self.session, target_datetime=datetime(year=2022, month=12, day=1)
        )
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "consumption": 30,
            },
        ] * 48
        self.assertEqual(len(data_list), len(expected_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(actual["zoneKey"], "AU-NT")
            self.assertEqual(actual["source"], "ntesmo.com.au")
            self.assertEqual(actual["consumption"], expected_data[index]["consumption"])

        # Check that the dates corresponds to two days:
        self.assertEqual(
            data_list[0]["datetime"],
            australia.localize(datetime(year=2022, month=12, day=1, hour=4, minute=30)),
        )
        self.assertEqual(
            data_list[-1]["datetime"],
            australia.localize(datetime(year=2022, month=12, day=2, hour=4, minute=00)),
        )
