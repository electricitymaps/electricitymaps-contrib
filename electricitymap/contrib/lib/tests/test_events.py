import logging
import math
from datetime import datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import freezegun
import numpy as np
import pytest

from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    Exchange,
    GridAlert,
    GridAlertType,
    LocationalMarginalPrice,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)
from electricitymap.contrib.lib.types import ZoneKey


def test_create_exchange():
    exchange = Exchange(
        zoneKey=ZoneKey("AT->DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        netFlow=1,
        source="trust.me",
    )
    assert exchange.zoneKey == ZoneKey("AT->DE")
    assert exchange.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert exchange.netFlow == 1
    assert exchange.source == "trust.me"

    exchange = Exchange(
        zoneKey=ZoneKey("AT->DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        netFlow=-1,
        source="trust.me",
    )
    assert exchange.netFlow == -1


def test_raises_if_invalid_exchange():
    # This should raise a ValueError because the netFlow is None.
    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=None,
            source="trust.me",
        )

    # This should raise a ValueError because the netFlow is NaN.
    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=math.nan,
            source="trust.me",
        )

    # This should raise a ValueError because the netFlow is Nan using Numpy.
    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=np.nan,
            source="trust.me",
        )

    # This should raise a ValueError because the timezone is missing.
    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1),
            netFlow=1,
            source="trust.me",
        )

    # This should raise a ValueError because the zoneKey is not an Exchange
    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )

    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("AT-DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )

    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("UNKNOWN->UNKNOWN"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )

    with pytest.raises(ValueError):
        Exchange(
            zoneKey=ZoneKey("DE->AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )


def test_exchange_static_create_logs_error():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        Exchange.create(
            logger=logger,
            zoneKey=ZoneKey("DER->FR"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=-1,
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_update_exchange():
    exchange = Exchange(
        zoneKey=ZoneKey("AT->DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        netFlow=1,
        source="trust.me",
    )
    new_exchange = Exchange(
        zoneKey=ZoneKey("AT->DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        netFlow=2,
        source="trust.me",
    )
    final_exchange = Exchange._update(exchange, new_exchange)
    assert final_exchange is not None
    assert final_exchange.netFlow == 2
    assert final_exchange.zoneKey == ZoneKey("AT->DE")
    assert final_exchange.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert final_exchange.source == "trust.me"


def test_create_consumption():
    consumption = TotalConsumption(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        consumption=1,
        source="trust.me",
    )
    assert consumption.zoneKey == ZoneKey("DE")
    assert consumption.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert consumption.consumption == 1
    assert consumption.source == "trust.me"


def test_raises_if_invalid_consumption():
    # This should raise a ValueError because the consumption is None.
    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=None,
            source="trust.me",
        )

    # This should raise a ValueError because the consumption is NaN.
    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=math.nan,
            source="trust.me",
        )

    # This should raise a ValueError because the consumption is Nan using Numpy.
    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=np.nan,
            source="trust.me",
        )

    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("ATT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1),
            consumption=1,
            source="trust.me",
        )
    with pytest.raises(ValueError):
        TotalConsumption(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=-1,
            source="trust.me",
        )


def test_static_create_logs_error():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        TotalConsumption.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=-1,
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_create_price():
    price = Price(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        price=1,
        source="trust.me",
        currency="EUR",
    )
    assert price.zoneKey == ZoneKey("DE")
    assert price.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert price.price == 1
    assert price.source == "trust.me"
    assert price.currency == "EUR"


def test_invalid_price_raises():
    # This should raise a ValueError because the price is None.
    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=None,
            source="trust.me",
            currency="EUR",
        )

    # This should raise a ValueError because the price is NaN.
    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=math.nan,
            source="trust.me",
            currency="EUR",
        )

    # This should raise a ValueError because the price is Nan using Numpy.
    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=np.nan,
            source="trust.me",
            currency="EUR",
        )

    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("ATT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="EUR",
        )
    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1),
            price=1,
            source="trust.me",
            currency="EUR",
        )
    with pytest.raises(ValueError):
        Price(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="EURO",
        )


@freezegun.freeze_time("2023-01-01")
def test_prices_can_be_in_future():
    Price(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
        price=1,
        source="trust.me",
        currency="EUR",
    )


def test_create_locational_marginal_price():
    lmp = LocationalMarginalPrice(
        zoneKey=ZoneKey("US-CENT-SWPP"),
        datetime=datetime(2025, 3, 1, tzinfo=timezone.utc),
        price=1,
        source="trust.me",
        currency="USD",
        node="SPPNORTH_HUB",
    )
    assert lmp.zoneKey == ZoneKey("US-CENT-SWPP")
    assert lmp.datetime == datetime(2025, 3, 1, tzinfo=timezone.utc)
    assert lmp.price == 1
    assert lmp.source == "trust.me"
    assert lmp.currency == "USD"
    assert lmp.node == "SPPNORTH_HUB"


@pytest.mark.parametrize(
    "node",
    [
        "",  # Empty string
        None,  # None value
        " ",  # Space only
        "\t",  # Tab only
        "\n",  # Newline only
        "   ",  # Multiple spaces
        " \t\n ",  # Mixed whitespace
        "\tSPPNORTH_HUB",  # Leading whitespace
        "SPPNORTH_HUB\t",  # Trailing whitespace
    ],
)
def test_invalid_locational_marginal_price_node_raises(node):
    # This should raise a ValueError because the node is a empty string.
    with pytest.raises(ValueError):
        LocationalMarginalPrice(
            zoneKey=ZoneKey("US-CENT-SWPP"),
            datetime=datetime(2025, 3, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="USD",
            node=node,
        )


def test_create_grid_alerts():
    grid_alert = GridAlert.create(
        logger=logging.Logger("test"),
        zoneKey=ZoneKey("US-MIDA-PJM"),
        locationRegion="Test Region",
        source="trust.me",
        alertType=GridAlertType.action,
        message="This is a test message",
        issuedTime=datetime(2025, 3, 1, tzinfo=timezone.utc),
        startTime=None,
        endTime=None,
    )
    assert grid_alert is not None
    assert grid_alert.zoneKey == ZoneKey("US-MIDA-PJM")
    assert grid_alert.locationRegion == "Test Region"
    assert grid_alert.source == "trust.me"
    assert grid_alert.alertType == GridAlertType.action
    assert grid_alert.message == "This is a test message"
    assert grid_alert.issuedTime == datetime(2025, 3, 1, tzinfo=timezone.utc)
    assert grid_alert.startTime == grid_alert.issuedTime  # because of the default
    assert grid_alert.endTime is None


def test_invalid_message_raises():
    # This should raise a ValueError because empty message
    with pytest.raises(ValueError):
        GridAlert(
            logger=logging.Logger("test"),
            zoneKey=ZoneKey("US-MIDA-PJM"),
            locationRegion=None,
            source="trust.me",
            alertType=GridAlertType.action,
            message="",
            issuedTime=datetime(2025, 3, 1, tzinfo=timezone.utc),
            startTime=None,
            endTime=None,
        )


def test_create_production_breakdown():
    mix = ProductionMix(wind=10)
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        production=mix,
        source="trust.me",
    )
    assert breakdown.zoneKey == ZoneKey("DE")
    assert breakdown.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert breakdown.production is not None
    assert breakdown.production.wind == 10
    assert breakdown.source == "trust.me"


def test_create_production_breakdown_with_storage():
    mix = ProductionMix(
        wind=10,
        hydro=20,
    )
    storage = StorageMix(
        hydro=10,
    )
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        production=mix,
        storage=storage,
        source="trust.me",
    )

    assert breakdown.production is not None
    assert breakdown.production.hydro == 20
    assert breakdown.storage is not None
    assert breakdown.storage.hydro == 10


def test_invalid_breakdown_raises():
    mix = ProductionMix(
        wind=10,
        hydro=20,
    )
    storage = StorageMix(
        hydro=10,
    )
    with pytest.raises(ValueError):
        ProductionBreakdown(
            zoneKey=ZoneKey("ATT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
        )
    with pytest.raises(ValueError):
        ProductionBreakdown(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1),
            production=mix,
            source="trust.me",
        )
    with pytest.raises(ValueError):
        ProductionBreakdown(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=None),
            storage=storage,
            source="trust.me",
        )


def test_negative_production_gets_corrected():
    mix = ProductionMix(
        wind=10,
        hydro=-20,
    )
    logger = logging.Logger("test")
    with patch.object(logger, "debug") as mock_logger:
        breakdown = ProductionBreakdown.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
        )
        mock_logger.assert_called_once()
        assert breakdown is not None
        assert breakdown.production is not None
        assert breakdown.production.hydro is None
        assert breakdown.production.wind == 10

        dict_form = breakdown.to_dict()
        assert dict_form["production"]["wind"] == 10
        assert dict_form["production"]["hydro"] is None


def test_self_report_negative_value():
    mix = ProductionMix()
    # We have manually set a 0 to avoid reporting self consumption for instance.
    mix.add_value("wind", 0)
    # This one has been set through the attributes and should be reported as None.
    mix.biomass = -10
    logger = logging.Logger("test")
    with patch.object(logger, "debug") as mock_logger:
        breakdown = ProductionBreakdown.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
        )
        mock_logger.assert_called_once()
        assert breakdown is not None
        assert breakdown.production is not None
        assert breakdown.production.wind == 0
        assert breakdown.production.biomass is None


def test_unknown_production_mode_raises():
    mix = ProductionMix()
    with pytest.raises(AttributeError):
        mix.add_value("nuke", 10)
    with pytest.raises(AttributeError):
        mix.nuke = 10
    storage = StorageMix()
    with pytest.raises(AttributeError):
        storage.add_value("nuke", 10)
    with pytest.raises(AttributeError):
        storage.nuke = 10


@freezegun.freeze_time("2023-01-01")
def test_forecasted_points():
    mix = ProductionMix(wind=10)
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 2, 1, tzinfo=timezone.utc),
        production=mix,
        source="trust.me",
        sourceType=EventSourceType.forecasted,
    )
    assert breakdown.zoneKey == ZoneKey("DE")
    assert breakdown.datetime == datetime(2023, 2, 1, tzinfo=timezone.utc)
    assert breakdown.production is not None
    assert breakdown.production.wind == 10
    assert breakdown.source == "trust.me"
    assert breakdown.sourceType == EventSourceType.forecasted


@freezegun.freeze_time("2023-01-01")
def test_non_forecasted_points_in_future():
    mix = ProductionMix(wind=10)
    with pytest.raises(ValueError):
        _breakdown = ProductionBreakdown(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 3, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
        )


@freezegun.freeze_time("2023-01-01")
def test_non_forecasted_point_with_timezone_forward():
    """Test that points in a timezone that is ahead of UTC are accepted."""
    mix = ProductionMix(wind=10)
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, 5, tzinfo=ZoneInfo("Asia/Tokyo")),
        production=mix,
        source="trust.me",
    )
    assert breakdown.datetime == datetime(2023, 1, 1, 5, tzinfo=ZoneInfo("Asia/Tokyo"))


def test_static_create_logs_error_with_none():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        ProductionBreakdown.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=None),
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_static_create_logs_with_nan():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        ProductionBreakdown.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=math.nan),
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_static_create_logs_with_nan_using_numpy():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        ProductionBreakdown.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=np.nan),
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_set_breakdown_all_present():
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        production=ProductionMix(wind=10, solar=None),
        source="trust.me",
    )
    dict_form = breakdown.to_dict()
    assert dict_form["production"].keys() == {"wind", "solar"}
    assert dict_form["production"]["wind"] == 10
    assert dict_form["production"]["solar"] is None


def test_set_modes_all_present_add_mode():
    mix = ProductionMix(wind=10)
    mix.add_value("solar", None)
    breakdown = ProductionBreakdown(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        production=mix,
        source="trust.me",
    )
    dict_form = breakdown.to_dict()
    assert dict_form["production"].keys() == {"wind", "solar"}
    assert dict_form["production"]["wind"] == 10
    assert dict_form["production"]["solar"] is None


def test_create_generation():
    generation = TotalProduction(
        zoneKey=ZoneKey("DE"),
        datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
        source="trust.me",
        value=1,
    )
    assert generation.zoneKey == ZoneKey("DE")
    assert generation.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
    assert generation.source == "trust.me"
    assert generation.value == 1


def test_total_production_static_create_logs_error():
    logger = logging.Logger("test")
    with patch.object(logger, "error") as mock_error:
        TotalProduction.create(
            logger=logger,
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=-1,
            source="trust.me",
        )
        mock_error.assert_called_once()


def test_raises_if_invalid_generation():
    # This should raise a ValueError because the generation is None.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=None,
            source="trust.me",
        )

    # This should raise a ValueError because the generation is NaN.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=math.nan,
            source="trust.me",
        )

    # This should raise a ValueError because the generation is Nan using Numpy.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=np.nan,
            source="trust.me",
        )

    # This should raise a ValueError because the timezone is missing.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1),
            value=1,
            source="trust.me",
        )

    # This should raise a ValueError because the zoneKey is not a ZoneKey.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("ATT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )

    # This should raise a ValueError because the value is negative.
    with pytest.raises(ValueError):
        TotalProduction(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=-1,
            source="trust.me",
        )


def test_production_mix_has_all_production_modes():
    mix = ProductionMix()
    for mode in PRODUCTION_MODES:
        assert hasattr(mix, mode)


def test_storage_mix_has_all_storage_modes():
    mix = StorageMix()
    for mode in STORAGE_MODES:
        assert hasattr(mix, mode)


def test_set_attr():
    mix = ProductionMix()
    mix.wind = 10
    assert mix.wind == 10


def test_set_attr_with_negative_value():
    mix = ProductionMix()
    mix.wind = -10
    assert mix.wind is None


def test_set_attr_with_none():
    mix = ProductionMix()
    mix.wind = None
    assert mix.wind is None


def test_set_attr_with_invalid_mode():
    mix = ProductionMix()
    with pytest.raises(AttributeError):
        mix.nuke = 10


def test_set_item():
    mix = ProductionMix()
    mix["wind"] = 10
    assert mix.wind == 10


def test_set_item_with_negative_value():
    mix = ProductionMix()
    mix["wind"] = -10
    assert mix.wind is None


def test_set_item_with_none():
    mix = ProductionMix()
    mix["wind"] = None
    assert mix.wind is None


def test_set_item_with_invalid_mode():
    mix = ProductionMix()
    with pytest.raises(AttributeError):
        mix["nuke"] = 10


def test_set_attr_storage():
    mix = StorageMix()
    mix.hydro = 10
    assert mix.hydro == 10


def test_set_attr_storage_with_negative_value():
    mix = StorageMix()
    mix.hydro = -10
    assert mix.hydro == -10


def test_set_attr_storage_with_none():
    mix = StorageMix()
    mix.hydro = None
    assert mix.hydro is None


def test_set_attr_storage_with_invalid_mode():
    mix = StorageMix()
    with pytest.raises(AttributeError):
        mix.nuke = 10


def test_set_item_storage():
    mix = StorageMix()
    mix["hydro"] = 10
    assert mix.hydro == 10


def test_set_item_storage_with_negative_value():
    mix = StorageMix()
    mix["hydro"] = -10
    assert mix.hydro == -10


def test_set_item_storage_with_none():
    mix = StorageMix()
    mix["hydro"] = None
    assert mix.hydro is None


def test_set_item_storage_with_invalid_mode():
    mix = StorageMix()
    with pytest.raises(AttributeError):
        mix["nuke"] = 10


def test_production():
    mix = ProductionMix()
    mix.add_value("wind", 10)
    assert mix.wind == 10
    mix.add_value("wind", 5)
    assert mix.wind == 15
    assert mix.corrected_negative_modes == set()


def test_production_with_negative_value():
    mix = ProductionMix()
    mix.add_value("wind", 10)
    assert mix.wind == 10
    mix.add_value("wind", -5)
    assert mix.wind == 10
    assert mix.corrected_negative_modes == {"wind"}


def test_production_with_negative_value_expect_none():
    mix = ProductionMix()
    mix.add_value("wind", -10)
    assert mix.wind is None
    assert mix.corrected_negative_modes == {"wind"}


def test_production_with_negative_value_and_correct_with_none():
    mix = ProductionMix()
    mix.add_value("wind", -10, correct_negative_with_zero=True)
    assert mix.wind == 0
    mix.add_value("wind", 15, correct_negative_with_zero=True)
    assert mix.wind == 15
    assert mix.corrected_negative_modes == {"wind"}


def test_production_with_none():
    mix = ProductionMix()
    mix.add_value("wind", 10)
    assert mix.wind == 10
    mix.add_value("wind", None)
    assert mix.wind == 10
    assert mix.corrected_negative_modes == set()


def test_production_with_nan():
    mix = ProductionMix()
    mix.add_value("wind", 10)
    assert mix.wind == 10
    mix.add_value("wind", math.nan)
    assert mix.wind == 10
    assert mix.corrected_negative_modes == set()


def test_production_with_nan_using_numpy():
    mix = ProductionMix()
    mix.add_value("wind", 10)
    assert mix.wind == 10
    mix.add_value("wind", np.nan)
    assert mix.wind == 10
    assert mix.corrected_negative_modes == set()


def test_production_with_nan_init():
    mix = ProductionMix(wind=math.nan)
    assert mix.wind is None


def test_production_with_nan_using_numpy_init():
    mix = ProductionMix(wind=np.nan)
    assert mix.wind is None


def test_storage():
    mix = StorageMix()
    mix.add_value("hydro", 10)
    assert mix.hydro == 10
    mix.add_value("hydro", 5)
    assert mix.hydro == 15


def test_storage_with_negative_value():
    mix = StorageMix()
    mix.add_value("hydro", 10)
    assert mix.hydro == 10
    mix.add_value("hydro", -5)
    assert mix.hydro == 5


def test_storage_with_none():
    mix = StorageMix()
    mix.add_value("hydro", None)
    assert mix.hydro is None
    mix.add_value("hydro", -5)
    assert mix.hydro == -5
    mix.add_value("hydro", None)
    assert mix.hydro == -5


def test_storage_with_nan():
    mix = StorageMix()
    mix.add_value("hydro", math.nan)
    assert mix.hydro is None
    mix.add_value("hydro", -5)
    assert mix.hydro == -5
    mix.add_value("hydro", math.nan)
    assert mix.hydro == -5


def test_storage_with_nan_using_numpy():
    mix = StorageMix()
    mix.add_value("hydro", np.nan)
    assert mix.hydro is None
    mix.add_value("hydro", -5)
    assert mix.hydro == -5
    mix.add_value("hydro", np.nan)
    assert mix.hydro == -5


def test_storage_with_nan_init():
    mix = StorageMix(hydro=math.nan)
    assert mix.hydro is None


def test_storage_with_nan_using_numpy_init():
    mix = StorageMix(hydro=np.nan)
    assert mix.hydro is None


def test_update_production():
    mix = ProductionMix(wind=10, solar=20)
    new_mix = ProductionMix(wind=5, solar=25)
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind == 5
    assert final_mix.solar == 25


def test_update_storage():
    mix = StorageMix(hydro=10, battery=20)
    new_mix = StorageMix(hydro=5, battery=25)
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro == 5
    assert final_mix.battery == 25


def test_update_production_with_none():
    mix = ProductionMix(wind=10, solar=20)
    new_mix = ProductionMix(wind=None, solar=25)
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind == 10
    assert final_mix.solar == 25


def test_update_storage_with_none():
    mix = StorageMix(hydro=10, battery=20)
    new_mix = StorageMix(hydro=None, battery=25)
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro == 10
    assert final_mix.battery == 25


def test_update_production_with_empty():
    mix = ProductionMix()
    new_mix = ProductionMix(wind=0, solar=25)
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind == 0
    assert final_mix.solar == 25


def test_update_storage_with_empty():
    mix = StorageMix()
    new_mix = StorageMix(hydro=0, battery=25)
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro == 0
    assert final_mix.battery == 25


def test_update_production_with_new_empty():
    mix = ProductionMix(wind=10, solar=20)
    new_mix = ProductionMix()
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind == 10
    assert final_mix.solar == 20


def test_update_storage_with_new_empty():
    mix = StorageMix(hydro=10, battery=20)
    new_mix = StorageMix()
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro == 10
    assert final_mix.battery == 20


def test_update_production_with_empty_and_new_none():
    mix = ProductionMix()
    new_mix = ProductionMix(wind=None, solar=None)
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind is None
    assert final_mix.solar is None


def test_update_storage_with_empty_and_new_none():
    mix = StorageMix()
    new_mix = StorageMix(hydro=None, battery=None)
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro is None
    assert final_mix.battery is None


def test_update_production_with_empty_and_new_empty():
    mix = ProductionMix()
    new_mix = ProductionMix()
    final_mix = ProductionMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.wind is None
    assert final_mix.solar is None


def test_update_storage_with_empty_and_new_empty():
    mix = StorageMix()
    new_mix = StorageMix()
    final_mix = StorageMix._update(mix, new_mix)
    assert final_mix is not None
    assert final_mix.hydro is None
    assert final_mix.battery is None
