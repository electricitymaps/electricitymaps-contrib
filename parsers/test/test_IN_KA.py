from importlib import resources

from requests_mock import GET

from parsers import IN_KA


def test_fetch_consumption(adapter, session):
    adapter.register_uri(
        GET,
        "https://kptclsldc.in/Default.aspx",
        text=resources.files("parsers.test.mocks")
        .joinpath("IN_KA_Default.html")
        .read_text(),
    )

    data = IN_KA.fetch_consumption("IN-KA", session)
    assert data
    assert data["zoneKey"] == "IN-KA"
    assert data["source"] == "kptclsldc.in"
    assert data["datetime"]
    assert data["consumption"]
    assert data["consumption"] == 7430.0


def test_fetch_production(adapter, session):
    adapter.register_uri(
        GET,
        "https://kptclsldc.in/StateGen.aspx",
        text=resources.files("parsers.test.mocks")
        .joinpath("IN_KA_StateGen.html")
        .read_text(),
    )
    adapter.register_uri(
        GET,
        "https://kptclsldc.in/StateNCEP.aspx",
        text=resources.files("parsers.test.mocks")
        .joinpath("IN_KA_StateNCEP.html")
        .read_text(),
    )

    data = IN_KA.fetch_production("IN-KA", session)
    assert data
    assert data["zoneKey"] == "IN-KA"
    assert data["source"] == "kptclsldc.in"
    assert data["datetime"]
    assert data["production"]
    assert data["production"]["hydro"] == 2434.0
    assert data["storage"]
