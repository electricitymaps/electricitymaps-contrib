from datetime import datetime
from json import loads

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import ES
from electricitymap.contrib.types import ZoneKey

MOCKS_DIR = "electricitymap/contrib/parsers/tests/mocks/ES"

# (zone_key, mock_filename, target_date) — one row per upstream system response.
ZONE_FIXTURES = [
    (ZoneKey("ES"), "demandaGeneracionPeninsula.json", "2024-10-26"),
    (ZoneKey("ES-IB-MA"), "demandaGeneracionBaleares.json", "2024-10-26"),
    (ZoneKey("ES-CN-TE"), "demandaGeneracionCanarias.json", "2024-10-26"),
    (ZoneKey("ES-CN-LZ"), "demandaGeneracionCanariasLanzarote.json", "2026-04-28"),
    (ZoneKey("ES-CE"), "demandaGeneracionPeninsulaCeuta.json", "2026-04-21"),
]


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    # The upstream payloads are JSONP-wrapped, not strictly valid JSON.
    for zone_key, filename, target_date in ZONE_FIXTURES:
        with open(f"{MOCKS_DIR}/{filename}", "rb") as data:
            requests_mock.register_uri(
                GET,
                ES.get_url(zone_key, target_date),
                content=data.read(),
            )

    with open(f"{MOCKS_DIR}/demandaGeneracionCanariasLaGomera.json", "rb") as data:
        requests_mock.register_uri(
            GET,
            ES.get_url(ZoneKey("ES-CN-IG"), "2026-08-01"),
            content=data.read(),
        )


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_consumption(requests_mock, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_consumption(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_production(requests_mock, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_production(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "mock_filename,target_date",
    [
        # Before 2022-01-24 REE only publishes the net "hid"; "turb"/"conb" are zero.
        ("demandaGeneracionCanariasElHierro2018.json", "2018-07-15"),
        # Since then "hid" == "turb" + "conb".
        ("demandaGeneracionCanariasElHierro2022.json", "2022-04-15"),
    ],
)
def test_fetch_production_el_hierro_hydro_storage(
    requests_mock, session, mock_filename, target_date
):
    zone_key = ZoneKey("ES-CN-HI")
    with open(f"{MOCKS_DIR}/{mock_filename}", "rb") as data:
        payload = data.read()
    requests_mock.register_uri(GET, ES.get_url(zone_key, target_date), content=payload)
    raw = loads(payload.decode()[5:-1])["valoresHorariosGeneracion"]

    events = ES.fetch_production(zone_key, session, datetime.fromisoformat(target_date))

    assert len(events) == len(raw)
    assert any(row["hid"] != 0 for row in raw)
    for event, row in zip(events, raw, strict=True):
        assert event["storage"]["hydro"] == pytest.approx(-row["hid"])
        assert event["production"].get("hydro") is None


@pytest.mark.parametrize(
    "zone_key1,zone_key2,target_date",
    [
        (ZoneKey("ES"), ZoneKey("PT"), "2024-10-26"),
        (ZoneKey("ES-IB-IZ"), ZoneKey("ES-IB-MA"), "2024-10-26"),
        (ZoneKey("ES-CN-FV"), ZoneKey("ES-CN-LZ"), "2026-04-28"),
        (ZoneKey("ES-CN-IG"), ZoneKey("ES-CN-TE"), "2026-08-01"),
    ],
    ids=["ES->PT", "ES-IB-IZ->ES-IB-MA", "ES-CN-FV->ES-CN-LZ", "ES-CN-IG->ES-CN-TE"],
)
def test_fetch_exchange(
    requests_mock, session, snapshot, zone_key1, zone_key2, target_date
):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_exchange(
        zone_key1, zone_key2, session, datetime.fromisoformat(target_date)
    )
