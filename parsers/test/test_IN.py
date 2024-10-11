import unittest

import arrow

from parsers.IN import get_start_of_day


class TestIN(unittest.TestCase):
    def test_get_start_of_day(self):
        # "2020-12-17 00:00:00+05:30" -> "2020-12-16 18:30:00+00:00"
        start_day = get_start_of_day(arrow.get("2020-12-16 18:30:00+00:00").datetime)
        assert start_day == arrow.get("2020-12-17 00:00:00+05:30").datetime
        # "2020-12-16 23:59:00+05:30" -> "2020-12-16 18:29:00+00:00"
        start_day = get_start_of_day(arrow.get("2020-12-16 18:29:00+00:00").datetime)
        assert start_day == arrow.get("2020-12-16 00:00:00+05:30").datetime
        # "2020-12-17 00:05:30+05:30" -> "2020-12-17 00:00:00+00:00"
        start_day = get_start_of_day(arrow.get("2020-12-17 00:00:00+00:00").datetime)
        assert start_day == arrow.get("2020-12-17 00:00:00+05:30").datetime


if __name__ == "__main__":
    unittest.main()
