"""Tests for validation.py."""
import logging
import unittest

from parsers.lib.validation import validate
from parsers.test.mocks.quality_check import *


class ProductionTestCase(unittest.TestCase):
    """Tests for validate"""

    test_logger = logging.getLogger()
    test_logger.setLevel(logging.ERROR)

    def test_all_zeros_or_null(self):
        validated = validate(datapoint=p15, logger=self.test_logger, fake_zeros=True)
        self.assertEqual(validated, None)


if __name__ == "__main__":
    unittest.main()
