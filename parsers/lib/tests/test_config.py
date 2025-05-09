from parsers.lib.config import ProductionModes, StorageModes


def test_ProductionModes_enum_values(snapshot):
    assert snapshot == ProductionModes.values()


def test_ProductionModes_enum_names(snapshot):
    assert snapshot == ProductionModes.names()


def test_ProductionModes_enum_items(snapshot):
    assert snapshot == ProductionModes.items()


def test_StorageModes_enum_values(snapshot):
    assert snapshot == StorageModes.values()


def test_StorageModes_enum_names(snapshot):
    assert snapshot == StorageModes.names()


def test_StorageModes_enum_items(snapshot):
    assert snapshot == StorageModes.items()
