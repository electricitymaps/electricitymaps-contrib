from datetime import datetime

from requests_mock import ANY

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ES


### El Hierro
# Consumption
def test_fetch_consumption(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2025-01-25 02:00","dem":4.8,"die":3.4,"gas":0.0,"eol":1.9,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.2,"conb":-0.5,"turb":0.3,"gnhd":-0.2,"efl":0.0}]})'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_consumption(
        ZoneKey("ES-CN-HI"), session, datetime.fromisoformat("2025-01-25")
    )


### El Hierro
# Production
def test_fetch_production_storage(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2025-01-25 02:00","dem":4.8,"die":3.4,"gas":0.0,"eol":1.9,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.2,"conb":-0.5,"turb":0.3,"gnhd":-0.2,"efl":0.0}]})'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-CN-HI"), session, datetime.fromisoformat("2025-01-25")
    )


### Menorca
# Production
def test_fetch_production(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2025-01-25 03:00","dem":31.1,"car":0.0,"die":0.0,"gas":20.6,"cc":0.0,"cb":0.0,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":10.5,"emi":-0.0,"otrRen":0.0,"resid":0.0,"genAux":0.0,"cogen":0.0,"eif":-0.0,"residNr":0.0,"residRen":0.0}]});'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-IB-ME"), session, datetime.fromisoformat("2025-01-25")
    )


### Mallorca
# Exchange
def test_fetch_exchange(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2025-01-25 03:00","dem":314.1,"car":0.0,"die":0.0,"gas":0.0,"cc":298.4,"cb":82.1,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-10.5,"emi":-70.5,"otrRen":1.3,"resid":0.0,"genAux":0.0,"cogen":3.2,"eif":-0.0,"residNr":5.1,"residRen":5.1}]});'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_exchange(
        ZoneKey("ES"),
        ZoneKey("ES-IB-MA"),
        session,
        datetime.fromisoformat("2025-01-25"),
    )
