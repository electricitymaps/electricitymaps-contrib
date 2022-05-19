import unittest

import arrow

from parsers.CH import get_solar_capacity_at


class TestCH(unittest.TestCase):
    def test_get_solar_capacity(self):
        assert get_solar_capacity_at(arrow.get("2018-01-02").datetime) == 2070
        assert (
            get_solar_capacity_at(arrow.get("2018-01-01 00:00:00+00:00").datetime)
            == 2070
        )
        assert get_solar_capacity_at(arrow.get("2014-02-01").datetime) == 1385
        assert get_solar_capacity_at(arrow.get("2022-01-01").datetime) == 3129


if __name__ == "__main__":
    unittest.main()
