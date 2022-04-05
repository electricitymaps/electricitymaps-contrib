"""Validate the CO2eq parameters."""

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
        for mode in eval(re.search(r"^const modeOrder = (\[$.*?^]);$",
                                   file_.read(),
                                   flags=re.DOTALL|re.MULTILINE)
                           .group(1)):
            if mode.endswith(" storage"):
                modes.update((mode.replace("storage", "charge"),
                              mode.replace("storage", "discharge")))
            else:
                modes.add(mode)
    return modes


class CO2eqParametersAll(unittest.TestCase):
    """A test case for the CO2eq parameters."""
    @classmethod
    def setUpClass(cls):
        cls.modes = get_possible_modes()
        with open("config/co2eq_parameters_all.json",
                  encoding="utf_8") as file_:
            cls.parameters = json.load(file_)

    @classmethod
    def check_power_origin_ratios(cls, callback):
        """Apply the callback to each 'powerOriginRatios' object in the CO2eq
        parameters.
        """
        # It is useful to keep `test_power_origin_modes_are_valid` and
        # `test_power_origin_ratios_sum_to_1` as separate tests, but they share
        # a lot of identical code. This helper function helps avoid code
        # duplication by factoring out the common logic and using a callback
        # function to handle the differences.
        fallback_zone_mixes = cls.parameters["fallbackZoneMixes"]
        for zone, mixes in (("defaults", fallback_zone_mixes["defaults"]),
                            *fallback_zone_mixes["zoneOverrides"].items()):
            power_origin_ratios = mixes["powerOriginRatios"]
            if isinstance(power_origin_ratios, list):
                for dictionary in power_origin_ratios:
                    callback(dictionary, zone)
            else:
                callback(power_origin_ratios, zone)

    def test_power_origin_modes_are_valid(self):
        """All modes in the 'powerOriginRatios' objects must be members of
        `self.modes`.
        """
        def assert_modes_are_valid(modes_to_ratios, zone):
            for mode, ratio in modes_to_ratios.items():
                if isinstance(ratio, numbers.Number):
                    self.assertIn(
                        mode,
                        self.modes,
                        msg=f"zone '{zone}' contains an invalid mode")

        self.check_power_origin_ratios(assert_modes_are_valid)

    def test_power_origin_ratios_sum_to_1(self):
        """All ratios in the 'powerOriginRatios' objects must sum to
        (approximately) 1.0.
        """
        def assert_ratios_sum_to_1(modes_to_ratios, zone):
            self.assertAlmostEqual(
                1.0,
                sum(ratio for ratio in modes_to_ratios.values()
                    if isinstance(ratio, numbers.Number)),
                msg=f"zone '{zone}' ratios do not sum to (approximately) 1.0",
                places=2)

        self.check_power_origin_ratios(assert_ratios_sum_to_1)

    def test_required_keys_are_present(self):
        """All objects must contain the required keys."""
        self.assertIn("fallbackZoneMixes", self.parameters)
        fallback_zone_mixes = self.parameters["fallbackZoneMixes"]
        self.assertIn("defaults", fallback_zone_mixes)
        self.assertIn("powerOriginRatios", fallback_zone_mixes["defaults"])
        self.assertIn("zoneOverrides", fallback_zone_mixes)
        for zone, mixes in fallback_zone_mixes["zoneOverrides"].items():
            self.assertIn("powerOriginRatios",
                          mixes,
                          msg=f"key missing from zone '{zone}'")


class CO2eqParametersDirectAndLifecycle:
    """A base class for the direct and lifecycle CO2eq parameters."""
    @classmethod
    def set_up_class(cls, filepath):
        """Initialise the class with the possible modes and parse the specified
        JSON file.
        """
        cls.modes = get_possible_modes()
        with open(filepath, encoding="utf_8") as file_:
            cls.parameters = json.load(file_)

    def test_emission_factor_modes_are_valid(self):
        """All modes in the 'emissionFactors' object's 'defaults' and
        'zoneOverrides' objects must be members of `self.modes`.
        """
        emission_factors = self.parameters["emissionFactors"]
        for zone, modes in (("defaults", emission_factors["defaults"]),
                            *emission_factors["zoneOverrides"].items()):
            for mode in modes:
                self.assertIn(mode,
                              self.modes,
                              msg=f"zone '{zone}' contains an invalid mode")

    def test_required_keys_are_present(self):
        """All objects must contain the required keys."""
        self.assertIn("emissionFactors", self.parameters)
        emission_factors = self.parameters["emissionFactors"]
        self.assertIn("defaults", emission_factors)
        self.assertIn("zoneOverrides", emission_factors)


class CO2eqParametersDirect(CO2eqParametersDirectAndLifecycle,
                            unittest.TestCase):
    """A test case for the direct CO2eq parameters."""
    @classmethod
    def setUpClass(cls):
        cls.set_up_class("config/co2eq_parameters_direct.json")


class CO2eqParametersLifecycle(CO2eqParametersDirectAndLifecycle,
                               unittest.TestCase):
    """A test case for the lifecycle CO2eq parameters."""
    @classmethod
    def setUpClass(cls):
        cls.set_up_class("config/co2eq_parameters_lifecycle.json")


if __name__ == "__main__":
    unittest.main(buffer=True)
