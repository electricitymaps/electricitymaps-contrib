"""Validate the CO2eq parameters."""

import datetime
import json
import numbers
import re
import unittest


def get_possible_modes():
    """Get the set of possible modes."""
    modes = set()
    with open("web/src/helpers/constants.js", encoding="utf-8") as file_:
        # The call to `eval` is a hack to parse the `modeOrder` array from the
        # JavaScript source file.
        for mode in eval(
            re.search(
                r"^const modeOrder = (\[$.*?^]);$",
                file_.read(),
                flags=re.DOTALL | re.MULTILINE,
            ).group(1)
        ):
            if mode.endswith(" storage"):
                modes.update(
                    (
                        mode.replace("storage", "charge"),
                        mode.replace("storage", "discharge"),
                    )
                )
            else:
                modes.add(mode)
    return modes


def parse_json_file(path):
    """Parse a JSON file."""
    with open(path, encoding="utf-8") as file_:
        return json.load(file_)


class CO2eqParametersAll(unittest.TestCase):
    """A test case for the CO2eq parameters."""

    modes = get_possible_modes()
    parameters = parse_json_file("config/co2eq_parameters_all.json")

    @staticmethod
    def check_valid_ratios_list(ratios):
        assert len(ratios) >= 1

    @classmethod
    def check_power_origin_ratios(cls, callback1, callback2):
        """Apply the callback to each ratio in the 'powerOriginRatios' objects."""
        # It is useful to keep `test_power_origin_modes_are_valid` and
        # `test_power_origin_ratios_sum_to_1` as separate tests, but they share
        # a lot of identical code. This helper function helps avoid code
        # duplication by factoring out the common logic and using callback
        # functions to handle the differences.
        fallback_zone_mixes = cls.parameters["fallbackZoneMixes"]
        for zone, mixes in (
            ("defaults", fallback_zone_mixes["defaults"]),
            *fallback_zone_mixes["zoneOverrides"].items(),
        ):
            ratios = mixes["powerOriginRatios"]
            if isinstance(ratios, list):
                cls.check_valid_ratios_list(ratios)
                for ratio in ratios:
                    callback1(ratio, zone)
            else:
                callback2(ratios, zone)

    @classmethod
    def check_contributions(cls, contribution_name, callback):
        """Apply the callback to each renewable/lowCarbon contribution."""
        contributions = cls.parameters[contribution_name]
        for zone, modes_to_contributions in (
            ("defaults", contributions["defaults"]),
            *contributions["zoneOverrides"].items(),
        ):
            for mode, c in modes_to_contributions.items():
                callback(mode, c, zone)

    @classmethod
    def check_is_renewable(cls, callback):
        """Apply the callback to each renewable contribution."""
        cls.check_contributions("isRenewable", callback)

    @classmethod
    def check_is_low_carbon(cls, callback):
        """Apply the callback to each lowCarbon contribution."""
        cls.check_contributions("isLowCarbon", callback)

    def test_power_origin_modes_are_valid(self):
        """All modes in the 'powerOriginRatios' objects must be valid."""

        def callback(ratio_, zone):
            for mode, ratio in ratio_["value"].items():
                if isinstance(ratio, numbers.Number):
                    self.assertIn(
                        mode, self.modes, msg=f"zone '{zone}' contains an invalid mode"
                    )

        self.check_power_origin_ratios(callback, callback)

    def test_power_origin_ratio_annual_lists_have_valid_dates(self):
        """Lists of power origin ratios must include valid date strings."""

        def callback(ratio, _zone):
            # An exception will be raised if the string is not a valid
            # datetime, thus failing the test.
            datetime.datetime.fromisoformat(ratio["datetime"])

        self.check_power_origin_ratios(callback, lambda ratio, zone: None)

    def test_power_origin_ratios_sum_to_1(self):
        """All ratios in the 'powerOriginRatios' objects must sum to
        (approximately) 1.0.
        """

        def callback(ratio, zone):
            self.assertAlmostEqual(
                1.0,
                sum(
                    ratio
                    for ratio in ratio["value"].values()
                    if isinstance(ratio, numbers.Number)
                ),
                msg=f"zone '{zone}' ratios do not sum to (approximately) 1.0",
                places=2,
            )

        self.check_power_origin_ratios(callback, callback)

    def test_required_keys_are_present(self):
        """All objects must contain the required keys."""

        def callback1(ratio, _zone):
            self.assertIn(
                "datetime",
                ratio,
                msg="lists of power origin ratios must include datetimes",
            )
            self.assertIn("value", ratio)

        def callback2(ratio, _zone):
            self.assertIn("value", ratio)

        self.assertIn("fallbackZoneMixes", self.parameters)
        fallback_zone_mixes = self.parameters["fallbackZoneMixes"]
        self.assertIn("defaults", fallback_zone_mixes)
        self.assertIn("powerOriginRatios", fallback_zone_mixes["defaults"])
        self.assertIn("zoneOverrides", fallback_zone_mixes)
        for zone, mixes in (
            ("defaults", fallback_zone_mixes["defaults"]),
            *fallback_zone_mixes["zoneOverrides"].items(),
        ):
            self.assertIn(
                "powerOriginRatios", mixes, msg=f"key missing from zone '{zone}'"
            )
        self.check_power_origin_ratios(callback1, callback2)

    def check_contribution_object(self, contribution, zone, mode, contribution_name):
        self.assertIn(
            "value",
            contribution.keys(),
            msg=f"zone '{zone}' does not contain a value for {contribution_name} contribution for mode {mode}",
        )
        self.assertTrue(
            0 <= contribution["value"] <= 1,
            msg=f"zone '{zone}' contains an invalid {contribution_name} contribution for mode {mode}",
        )

    def check_contribution_datetimes(self, contribution, zone, mode, contribution_name):
        # Would throw a KeyError if a member misses a datetime
        try:
            dts = [c["datetime"] for c in contribution]
        except KeyError:
            self.assertTrue(
                False,
                msg=f"zone '{zone}' is missing datetimes for the {contribution_name} contributions for mode {mode}",
            )
        try:
            dts = [datetime.datetime.fromisoformat(dt) for dt in dts]
        except ValueError:
            self.assertTrue(
                False,
                msg=f"zone '{zone}' contains invalid datetimes for the {contribution_name} contributions for mode {mode}",
            )
        self.assertEqual(
            dts,
            sorted(dts),
            msg=f"zone '{zone}' datetimes for the {contribution_name} contributions for mode {mode} are not ordered",
        )

    def test_is_renewable_valid_datetimes(self):
        def callback(mode, contribution, zone):
            if isinstance(contribution, list):
                self.check_contribution_datetimes(
                    contribution, zone, mode, "isRenewable"
                )

        self.check_is_renewable(callback)

    def test_is_renewable_valid_contributions(self):
        contribution_name = "isRenewable"

        def callback(mode, contribution, zone):
            if isinstance(contribution, list):
                for c in contribution:
                    self.check_contribution_object(c, zone, mode, contribution_name)
            else:
                self.check_contribution_object(
                    contribution, zone, mode, contribution_name
                )

        self.check_is_renewable(callback)

    def test_is_low_carbon_valid_datetimes(self):
        def callback(mode, contribution, zone):
            if isinstance(contribution, list):
                self.check_contribution_datetimes(
                    contribution, zone, mode, "isLowCarbon"
                )

        self.check_is_low_carbon(callback)

    def test_is_low_carbon_valid_contributions(self):
        contribution_name = "isLowCarbon"

        def callback(mode, contribution, zone):

            if isinstance(contribution, list):
                for c in contribution:
                    self.check_contribution_object(c, zone, mode, contribution_name)
            else:
                self.check_contribution_object(
                    contribution, zone, mode, contribution_name
                )

        self.check_is_low_carbon(callback)


class CO2eqParametersDirectAndLifecycleMixin:
    """A mixin for the direct and lifecycle CO2eq parameters."""

    modes = get_possible_modes()

    @classmethod
    def check_emission_factors(cls, callback):
        """Apply the callback to each emission factor in the 'emissionFactors'
        object.
        """
        emission_factors = cls.parameters["emissionFactors"]
        for zone, modes_to_factors in (
            ("defaults", emission_factors["defaults"]),
            *emission_factors["zoneOverrides"].items(),
        ):
            for mode, factors in modes_to_factors.items():
                callback(mode, factors, zone)

    def test_emission_factor_modes_are_valid(self):
        """All specified modes must be in the allowed set of modes."""

        def callback(mode, _factors, zone):
            self.assertIn(
                mode, self.modes, msg=f"zone '{zone}' contains an invalid mode"
            )

        self.check_emission_factors(callback)

    def test_emission_factor_annual_lists_have_valid_dates(self):
        """Lists of emission factors must include valid date strings."""

        def callback(_mode, factors, _zone):
            if isinstance(factors, list):
                for factor in factors:
                    # An exception will be raised if the string is not a valid
                    # datetime, thus failing the test.
                    datetime.datetime.fromisoformat(factor["datetime"])

        self.check_emission_factors(callback)

    def test_emission_factor_annual_lists_are_not_empty(self):
        """Verifies that the list of annual emission factors are not empty"""

        def callback(_mode, factors, _zone):
            if isinstance(factors, list):
                self.assertGreater(
                    len(factors),
                    0,
                    msg=f"emission factors list is empty for zone {_zone}",
                )

        self.check_emission_factors(callback)

    def test_required_keys_are_present(self):
        """All objects must contain the required keys."""

        def callback(_mode, factors, _zone):
            if isinstance(factors, list):
                for factor in factors:
                    self.assertIn(
                        "datetime",
                        factor,
                        msg="lists of emission factors must include datetimes",
                    )
                    self.assertIn("value", factor)
            else:
                self.assertIn("value", factors)

        self.assertIn("emissionFactors", self.parameters)
        emission_factors = self.parameters["emissionFactors"]
        self.assertIn("defaults", emission_factors)
        self.assertIn("zoneOverrides", emission_factors)
        self.check_emission_factors(callback)


class CO2eqParametersDirect(CO2eqParametersDirectAndLifecycleMixin, unittest.TestCase):
    """A test case for the direct CO2eq parameters."""

    parameters = parse_json_file("config/co2eq_parameters_direct.json")


class CO2eqParametersLifecycle(
    CO2eqParametersDirectAndLifecycleMixin, unittest.TestCase
):
    """A test case for the lifecycle CO2eq parameters."""

    parameters = parse_json_file("config/co2eq_parameters_lifecycle.json")


if __name__ == "__main__":
    unittest.main(buffer=True)
