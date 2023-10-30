import unittest

from electricitymap.contrib.capacity_parsers.IRENA import (
    IRENA_JSON_TO_MODE_MAPPING,
    reallocate_capacity_mode,
)


class TestIRENA(unittest.TestCase):
    def test_reallocate_capacity_mode(self):
        zone_key = "IS"
        mode = 16
        assert reallocate_capacity_mode(zone_key, mode) == "oil"

        zone_key = "IS"
        mode = 1
        assert (
            reallocate_capacity_mode(zone_key, mode) == IRENA_JSON_TO_MODE_MAPPING[mode]
        )

        zone_key = "NI"
        mode = 1
        assert (
            reallocate_capacity_mode(zone_key, mode) == IRENA_JSON_TO_MODE_MAPPING[mode]
        )


if __name__ == "__main__":
    unittest.main()
