# Em tests/contrib/capacity_parsers/test_EMBER.py
import pandas as pd
import pytest

# A importação correta, considerando a estrutura do projeto
from electricitymap.contrib.capacity_parsers.EMBER import _ember_production_mode_mapper

# Dados "mockados" para garantir que os testes sejam independentes e determinísticos
MOCKED_SPECIFIC_MAPPING = {
    "FR": {"nuclear": "nuclear_fr", "éolien": "wind"}
}
MOCKED_ENERGIES = ["solar", "wind", "gas", "nuclear"]


# CT1: Teste de mapeamento específico bem-sucedido (Cobre a linha 1 da Tabela Verdade)
def test_specific_mapping_success(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", MOCKED_SPECIFIC_MAPPING)
    row = pd.Series({"zone_key": "FR", "mode": "éolien"})
    assert _ember_production_mode_mapper(row) == "wind"

# CT2: Zona correta, mas modo não está no mapeamento específico (Cobre a linha 2 da Tabela Verdade)
def test_specific_mapping_zone_match_mode_fail(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", MOCKED_SPECIFIC_MAPPING)
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.ENERGIES", MOCKED_ENERGIES)
    row = pd.Series({"zone_key": "FR", "mode": "gas"})
    assert _ember_production_mode_mapper(row) == "gas"

# CT3: Zona não está no mapeamento específico (Cobre a linha 3 da Tabela Verdade)
def test_specific_mapping_zone_fail(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", MOCKED_SPECIFIC_MAPPING)
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.ENERGIES", MOCKED_ENERGIES)
    row = pd.Series({"zone_key": "DE", "mode": "nuclear"})
    assert _ember_production_mode_mapper(row) == "nuclear"

# CT4: Mapeamento genérico de energia
def test_generic_energy_mapping(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", {})
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.ENERGIES", MOCKED_ENERGIES)
    row = pd.Series({"zone_key": "ANY", "mode": "solar"})
    assert _ember_production_mode_mapper(row) == "solar"

# CT5: Mapeamento do 'ember_mapper'
def test_ember_mapper_mapping(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", {})
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.ENERGIES", '')
    row = pd.Series({"zone_key": "ANY", "mode": "bioenergy"})
    assert _ember_production_mode_mapper(row) == "biomass"

# CT6: Modo desconhecido
def test_unknown_mapping(monkeypatch):
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.SPECIFIC_MODE_MAPPING", {})
    monkeypatch.setattr("electricitymap.contrib.capacity_parsers.EMBER.ENERGIES", '')
    row = pd.Series({"zone_key": "ANY", "mode": "exotic_energy"})
    assert _ember_production_mode_mapper(row) == "unknown"

# CT7: Entrada não é string
def test_non_string_input():
    row = pd.Series({"mode": None})
    assert _ember_production_mode_mapper(row) is None