import unittest

from scripts.update_capacity_configuration import (
    get_aggregated_capacity_config_dict,
    get_aggregated_capacity_config_list,
    get_zone_capacity_config,
    get_zone_capacity_list,
)


class updateCapacityConfigurationTestCase(unittest.TestCase):
    def test_capacity_config(self):
        capacity_config = {
            "wind": 1,
            "solar": {
                "datetime": "2022-01-01",
                "source": "abc",
                "value": 2,
            },
            "biomass": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 4,
                },
            ],
            "unknown": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2022-10-01",
                    "source": "abc",
                    "value": 4,
                },
            ],
        }
        data = {
            "wind": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 3,
            },
            "solar": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 4,
            },
            "biomass": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 5,
            },
            "hydro": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 6,
            },
            "unknown": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 5,
            },
        }

        expected = {
            "wind": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 3,
            },
            "solar": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 2,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 4,
                },
            ],
            "biomass": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 5,
                },
            ],
            "hydro": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 6,
            },
            "unknown": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2022-10-01",
                    "source": "abc",
                    "value": 4,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 5,
                },
            ],
        }

        self.assertEqual(get_zone_capacity_config(capacity_config, data), expected)

    def test_get_zone_capacity_list(self):
        capacity_config = {
            "biomass": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 4,
                },
            ],
            "unknown": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2022-10-01",
                    "source": "abc",
                    "value": 4,
                },
            ],
        }

        data = {
            "biomass": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 5,
            },
            "unknown": {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 5,
            },
        }

        expected = {
            "biomass": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 5,
                },
            ],
            "unknown": [
                {
                    "datetime": "2022-01-01",
                    "source": "abc",
                    "value": 3,
                },
                {
                    "datetime": "2022-10-01",
                    "source": "abc",
                    "value": 4,
                },
                {
                    "datetime": "2023-01-01",
                    "source": "abc",
                    "value": 5,
                },
            ],
        }

        self.assertEqual(
            get_zone_capacity_list("unknown", capacity_config, data),
            expected["unknown"],
        )
        self.assertEqual(
            get_zone_capacity_list("biomass", capacity_config, data),
            expected["biomass"],
        )

    def test_get_aggregated_capacity_config_dict(self):
        capacity_config = [
            {"datetime": "2023-01-01", "source": "abc", "value": 3},
            {"datetime": "2023-01-01", "source": "abc", "value": 4},
        ]
        capacity_config_2 = [
            {"datetime": "2022-01-01", "source": "abc", "value": 3},
            {"datetime": "2023-01-01", "source": "abc", "value": 4},
        ]

        expected = {
            "datetime": "2023-01-01",
            "source": "abc",
            "value": 7,
        }

        self.assertEqual(
            get_aggregated_capacity_config_dict(capacity_config, "parent_zone"),
            expected,
        )
        self.assertEqual(
            get_aggregated_capacity_config_dict(capacity_config_2, "parent_zone"),
            None,
        )

    def test_get_aggregated_capacity_config_list(self):
        capacity_config = [
            [
                {"datetime": "2022-01-01", "source": "abc", "value": 3},
                {"datetime": "2023-01-01", "source": "abc", "value": 4},
            ],
            [
                {"datetime": "2022-01-01", "source": "abc", "value": 9},
                {"datetime": "2023-01-01", "source": "abc", "value": 2},
            ],
            [
                {"datetime": "2022-01-01", "source": "abc", "value": 4},
                {"datetime": "2022-10-01", "source": "abc", "value": 5},
                {"datetime": "2023-01-01", "source": "abc", "value": 6},
            ],
        ]

        expected = [
            {
                "datetime": "2023-01-01",
                "source": "abc",
                "value": 12,
            },
            {
                "datetime": "2022-01-01",
                "source": "abc",
                "value": 16,
            },
        ]

        self.assertEqual(
            get_aggregated_capacity_config_list(capacity_config, "DK"),
            expected,
        )
