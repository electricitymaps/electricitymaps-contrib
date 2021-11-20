import datetime
import unittest

from requests import Session

from parsers import FR_O


class TestFRO(unittest.TestCase):
    def setUp(self):
        self.session = Session()

    def test_current_fetch_production(self):
        current_prod = FR_O.fetch_production("RE", session=self.session)

        last_prod = current_prod[0]["production"]
        self.assertGreater(last_prod["hydro"], 5)
        self.assertGreater(last_prod["coal"], 5)
        self.assertGreater(last_prod["biomass"], 5)
        self.assertGreater(last_prod["oil"], 5)

    def test_fixed_fetch_production_re(self):
        date = datetime.datetime(2020, 5, 20)
        current_prod = FR_O.fetch_production(
            "RE", target_datetime=date, session=self.session
        )

        last_prod = current_prod[0]["production"]
        self.assertEqual(last_prod["hydro"], 78.52)
        self.assertEqual(last_prod["coal"], 146.75)
        self.assertEqual(last_prod["biomass"], 1.43)
        self.assertEqual(last_prod["oil"], 105.12)

    def test_fixed_fetch_production_gp(self):
        date = datetime.datetime(2020, 5, 20)
        current_prod = FR_O.fetch_production(
            "GP", target_datetime=date, session=self.session
        )

        last_prod = current_prod[0]["production"]
        self.assertEqual(last_prod["hydro"], 2.96)
        self.assertEqual(last_prod["coal"], 34.97)
        self.assertEqual(last_prod["biomass"], 1.06)
        self.assertEqual(last_prod["oil"], 119.8)

    def test_fetch_price(self):
        date = datetime.datetime(2018, 5, 20)
        price_data = FR_O.fetch_price("RE", target_datetime=date, session=self.session)

        self.assertEqual(
            (
                price_data["datetime"].year,
                price_data["datetime"].month,
                price_data["datetime"].day,
            ),
            (
                date.year,
                date.month,
                date.day,
            ),
        )

        self.assertGreater(price_data["price"], 100)

    def tearDown(self):
        self.session.close()


if __name__ == "__main__":
    unittest.main()
