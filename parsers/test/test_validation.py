import logging

from parsers.lib.validation import validate
from parsers.test.mocks.quality_check import p15


def test_all_zeros_or_null():
    test_logger = logging.getLogger("test")
    test_logger.setLevel(logging.ERROR)
    assert validate(datapoint=p15, logger=test_logger, fake_zeros=True) is None
