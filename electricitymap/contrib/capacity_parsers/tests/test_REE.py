from datetime import datetime

from electricitymap.contrib.capacity_parsers import REE


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse):
        self._response = response
        self.last_call = None

    def get(self, url, params=None):
        self.last_call = (url, params)
        return self._response


def _patch_minimal_mappings(monkeypatch):
    """
    Para tornar o teste independente do conteúdo real de REE.py,
    reduzimos os dicionários a um caso mínimo estável.
    """
    monkeypatch.setattr(REE, "ZONE_KEY_TO_GEO_LIMIT", {"ES": "system"}, raising=False)
    monkeypatch.setattr(REE, "GEO_LIMIT_TO_GEO_IDS", {"system": "es"}, raising=False)
    # Mapeamento mínimo de tipos → modes
    monkeypatch.setattr(
        REE,
        "MODE_MAPPING",
        {
            "solar": "solar",
            "hydro": "hydro",
        },
        raising=False,
    )


# CT1 — C1=V, C2=V, C3=V → agrega
def test_fetch_production_capacity_aggregate_when_mode_exists(monkeypatch):
    _patch_minimal_mappings(monkeypatch)

    payload = {
        "included": [
            {"type": "solar", "attributes": {"values": [{"value": 60.4}]}},
            {"type": "solar", "attributes": {"values": [{"value": 39.6}]}},
        ]
    }
    session = FakeSession(FakeResponse(200, payload))

    zone_key = "ES"
    dt = datetime(2025, 5, 15, 13, 0, 0)

    result = REE.fetch_production_capacity(zone_key, dt, session)

    assert isinstance(result, dict)
    assert "solar" in result
    assert result["solar"]["value"] == 100.0
    assert result["solar"]["datetime"] == "2025-05-15"
    assert result["solar"]["source"] == "ree.es"


# CT2 — C1=V, C2=V, C3=F → inicializa
def test_fetch_production_capacity_initialize_when_first_occurrence(monkeypatch):
    _patch_minimal_mappings(monkeypatch)

    payload = {
        "included": [{"type": "hydro", "attributes": {"values": [{"value": 10.2}]}}]
    }
    session = FakeSession(FakeResponse(200, payload))

    zone_key = "ES"
    dt = datetime(2025, 5, 15, 13, 0, 0)

    result = REE.fetch_production_capacity(zone_key, dt, session)

    assert isinstance(result, dict)
    assert "hydro" in result
    assert result["hydro"]["value"] == 10.0  # 10.2 -> 10.0
    assert result["hydro"]["datetime"] == "2025-05-15"
    assert result["hydro"]["source"] == "ree.es"


# CT3 — C1=V, C2=F → item ignorado (capacity = {})
def test_fetch_production_capacity_ignores_unmapped_type(monkeypatch):
    _patch_minimal_mappings(monkeypatch)

    payload = {
        "included": [
            {"type": "unknown_type", "attributes": {"values": [{"value": 123.0}]}}
        ]
    }
    session = FakeSession(FakeResponse(200, payload))

    zone_key = "ES"
    dt = datetime(2025, 5, 15, 13, 0, 0)

    result = REE.fetch_production_capacity(zone_key, dt, session)

    assert isinstance(result, dict)
    assert result == {}  # nenhum item válido processado


# CT4 — C1=F → não processa (retorna None)
def test_fetch_production_capacity_returns_none_on_non_200(monkeypatch):
    _patch_minimal_mappings(monkeypatch)

    session = FakeSession(FakeResponse(404, {}))

    zone_key = "ES"
    dt = datetime(2025, 5, 15, 13, 0, 0)

    result = REE.fetch_production_capacity(zone_key, dt, session)

    assert result is None
