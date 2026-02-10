
import pytest
from datetime import datetime, timedelta
from unittest.mock import ANY


from electricitymap.contrib.parsers.lib.exceptions import ParserException

PATCH_PATH = "electricitymap.contrib.parsers.VN" 


class ZoneKey:
    def __init__(self, zone): self.zone = zone
    def __eq__(self, other): 
        if isinstance(other, ZoneKey): return self.zone == other.zone
        return self.zone == other
    def __hash__(self): return hash(self.zone)
    def __str__(self): return self.zone

class Session: pass 

from electricitymap.contrib.parsers.VN import fetch_consumption 


MOCKED_NOW = datetime(2025, 10, 31, 10, 0, 0)
EXPECTED_YESTERDAY = MOCKED_NOW - timedelta(days=1)

@pytest.fixture(autouse=True)
def mock_dependencies(mocker):
    
    mocker.patch(f"{PATCH_PATH}.datetime", mocker.MagicMock(wraps=datetime))
    mocker.patch(f"{PATCH_PATH}.datetime.now", return_value=MOCKED_NOW)
    mocker.patch(f"{PATCH_PATH}.timedelta", timedelta)
    
    mocker.patch(f"{PATCH_PATH}.fetch_live_consumption", autospec=True)
    mocker.patch(f"{PATCH_PATH}.fetch_historical_consumption", autospec=True)
    
    mocker.patch(f"{PATCH_PATH}.Session")

def test_ct1_live_data_valida(mocker):
    expected_data = [{"time": "now"}]
    
    live_mock = mocker.patch(
        f"{PATCH_PATH}.fetch_live_consumption", 
        return_value=expected_data
    )
    historical_mock = mocker.patch(f"{PATCH_PATH}.fetch_historical_consumption")
    
    result = fetch_consumption(zone_key=ZoneKey("FR"))
    
    assert result == expected_data
    live_mock.assert_called_once()
    historical_mock.assert_not_called()


def test_ct2_live_data_vazia_zona_vn(mocker):
    expected_historical_data = [{"time": "yesterday"}]
    
    mocker.patch(f"{PATCH_PATH}.fetch_live_consumption", return_value=[])
    
    historical_mock = mocker.patch(
        f"{PATCH_PATH}.fetch_historical_consumption",
        return_value=expected_historical_data
    )
    
    result = fetch_consumption(zone_key=ZoneKey("VN"))
    
    assert result == expected_historical_data
    historical_mock.assert_called_once_with(EXPECTED_YESTERDAY, ANY, ANY)


def test_ct3_live_data_vazia_zona_diferente(mocker):
    mocker.patch(f"{PATCH_PATH}.fetch_live_consumption", return_value=[])
    
    with pytest.raises(ParserException) as excinfo:
        fetch_consumption(zone_key=ZoneKey("US"))
        
    assert "No real time data found" in str(excinfo.value)
    mocker.patch(f"{PATCH_PATH}.fetch_historical_consumption").assert_not_called()


def test_ct4_historico_solicitado_vn(mocker):
    past_date = datetime(2024, 1, 1, 12, 0)
    expected_data = [{"hist": "passed_date"}]

    historical_mock = mocker.patch(
        f"{PATCH_PATH}.fetch_historical_consumption", 
        return_value=expected_data
    )
    
    result = fetch_consumption(zone_key=ZoneKey("VN"), target_datetime=past_date)
    
    assert result == expected_data
    historical_mock.assert_called_once_with(past_date, ANY, ANY)


def test_ct5_historico_solicitado_outra_zona(mocker):
    past_date = datetime(2024, 1, 1, 12, 0)
    
    with pytest.raises(NotImplementedError) as excinfo:
        fetch_consumption(zone_key=ZoneKey("US"), target_datetime=past_date)
        
    assert "This parser is not yet able to parse past dates for this zone" in str(excinfo.value)
    mocker.patch(f"{PATCH_PATH}.fetch_historical_consumption").assert_not_called()
    mocker.patch(f"{PATCH_PATH}.fetch_live_consumption").assert_not_called()