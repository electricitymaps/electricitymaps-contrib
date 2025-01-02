import unittest

from bs4 import BeautifulSoup

from parsers.lib import IN


class TestIndia(unittest.TestCase):
    def test_read_datetime_from_span_id(self):
        html_span = '<p><span id="lbldate">9/4/2017 5:17:00 PM</span></p>'
        html = BeautifulSoup(html_span, "html.parser")
        india_date_time = IN.read_datetime_from_span_id(
            html, "lbldate", "%d/%m/%Y %I:%M:%S %p"
        )
        self.assertIsNotNone(india_date_time)
        self.assertEqual(india_date_time.isoformat(), "2017-04-09T17:17:00+05:30")

        html_span = '<p><span id="lblPowerStatusDate">04-09-2017 17:13</span></p>'
        html = BeautifulSoup(html_span, "html.parser")
        india_date_time = IN.read_datetime_from_span_id(
            html, "lblPowerStatusDate", "%d-%m-%Y %H:%M"
        )
        self.assertIsNotNone(india_date_time)
        self.assertEqual(india_date_time.isoformat(), "2017-09-04T17:13:00+05:30")

    def test_read_text_from_span_id(self):
        html_span = '<span id="lblcgs" style="font-weight:bold;">2998</span>'
        html = BeautifulSoup(html_span, "html.parser")
        cgs_value = IN.read_text_from_span_id(html, "lblcgs")
        self.assertIsNotNone(cgs_value)
        self.assertEqual(cgs_value, "2998")

    def test_read_value_from_span_id(self):
        html_span = '<span id="lblcgs" style="font-weight:bold;">2998</span>'
        html = BeautifulSoup(html_span, "html.parser")
        cgs_value = IN.read_value_from_span_id(html, "lblcgs")
        self.assertIsNotNone(cgs_value)
        self.assertEqual(cgs_value, 2998.0)


if __name__ == "__main__":
    unittest.main()
