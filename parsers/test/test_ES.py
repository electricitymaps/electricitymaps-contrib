from datetime import datetime

from requests_mock import ANY

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ES


### El Hierro
# Consumption
def test_fetch_consumption(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2023-09-04 00:55","dem":5.5,"die":3.2,"gas":0.0,"eol":3.0,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.5}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_consumption(
        ZoneKey("ES-CN-HI"), session, datetime.fromisoformat("2023-09-04")
    )


### El Hierro
# Production
def test_fetch_production_storage(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2023-09-04 00:55","dem":5.5,"die":3.2,"gas":0.0,"eol":3.0,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.5}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-CN-HI"),
        session,
        datetime.fromisoformat("2023-09-04"),
    )


# Test for DST change days
def test_production_DST_CN(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2021-10-31 1A:55","dem":4.8,"die":2.8,"gas":0.0,"eol":3.3,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-1.2},{"ts":"2021-10-31 1B:00","dem":4.5,"die":2.5,"gas":0.0,"eol":3.2,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-1.2}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-CN-HI"),
        session,
        datetime.fromisoformat("2021-10-31"),
    )


### Menorca
# Production
def test_fetch_production(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2023-09-02 21:00","dem":85.9,"car":0.0,"die":22.6,"gas":59.3,"cc":0.0,"cb":0.0,"fot":1.1,"tnr":0.0,"trn":0.0,"eol":0.2,"emm":2.7,"emi":-0.0,"otrRen":0.0,"resid":0.0,"genAux":0.0,"cogen":0.0,"eif":-0.0}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-IB-ME"),
        session,
        datetime.fromisoformat("2023-09-03"),
    )


### Mallorca
# Exchange
def test_fetch_exchange(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2023-09-03 19:05","dem":670.3,"car":0.0,"die":0.0,"gas":0.0,"cc":416.4,"cb":309.8,"fot":19.7,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-20.6,"emi":-91.3,"otrRen":0.0,"resid":34.6,"genAux":0.0,"cogen":1.7,"eif":-0.0}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_exchange(
        ZoneKey("ES"),
        ZoneKey("ES-IB-MA"),
        session,
        datetime.fromisoformat("2023-09-03"),
    )


# Test for DST change days
def test_production_DST_IB(adapter, session, snapshot):
    mock_data = b'null({"valoresHorariosGeneracion":[{"ts":"2020-10-25 2A:55","dem":261.3,"car":73.3,"die":0.0,"gas":0.0,"cc":127.1,"cb":100.4,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-3.5,"emi":-58.1,"otrRen":0.0,"resid":19.2,"genAux":0.0,"cogen":2.9,"eif":-0.0},{"ts":"2020-10-25 2B:00","dem":261.7,"car":73.3,"die":0.0,"gas":0.0,"cc":128.0,"cb":100.4,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-3.3,"emi":-58.1,"otrRen":0.0,"resid":18.5,"genAux":0.0,"cogen":2.9,"eif":-0.0}]}'
    adapter.register_uri(ANY, ANY, content=mock_data)

    assert snapshot == ES.fetch_production(
        ZoneKey("ES-IB-MA"),
        session,
        datetime.fromisoformat("2020-10-25"),
    )
