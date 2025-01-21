#!/usr/bin/python

"""Tests for validation in ENTSOE parser."""

import logging

from parsers.ENTSOE import validate_production
from parsers.test.mocks.quality_check import p11, p12, p14

test_logger = logging.getLogger()
test_logger.setLevel(logging.ERROR)


def test_production_too_low_in_PL():
    validated = validate_production(p11, test_logger)
    assert validated is None


def test_production_too_high_in_SI():
    validated = validate_production(p12, test_logger)
    assert validated is None


def test_valid_production_in_FI():
    validated = validate_production(p14, test_logger)
    if isinstance(validated, dict):
        assert validated
        assert "production" in validated
        assert "hydro" in validated["production"]
