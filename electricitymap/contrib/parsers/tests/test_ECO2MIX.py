from electricitymap.contrib.parsers.ECO2MIX import (
    parse_exchange_to_df,
    parse_production_to_df,
)

# The day the clock jumps forward: local 02:00-02:45 never happens.
SPRING_DAY = "2025-03-30"
# The day the clock jumps back: local 02:00-02:45 happens twice.
AUTUMN_DAY = "2025-10-26"

# Quarter hours 01:45, 02:00, 02:15, 02:30, 02:45 and 03:00. RTE reports all
# six of them on every day, including the transition days.
PERIODES = {7: "100", 8: "200", 9: "300", 10: "400", 11: "500", 12: "600"}


def _payload(date: str, v: str, perimetre: str) -> str:
    valeurs = "".join(
        f"<valeur periode='{periode}'>{value}</valeur>"
        for periode, value in PERIODES.items()
    )
    return (
        f"<liste><mixtr date='{date}'>"
        f"<type v='{v}' perimetre='{perimetre}' granularite='Global' qual='1'>"
        f"{valeurs}</type></mixtr></liste>"
    )


def test_exchange_spring_gap_keeps_existing_slots_only():
    df = parse_exchange_to_df(_payload(SPRING_DAY, "Import_DE", "ACA"))
    assert [str(ts) for ts in df.index] == [
        "2025-03-30 01:45:00+01:00",
        "2025-03-30 03:00:00+02:00",
    ]
    assert list(df.net_flow) == [100.0, 600.0]


def test_exchange_autumn_repeat_is_not_placed_on_the_timeline_twice():
    df = parse_exchange_to_df(_payload(AUTUMN_DAY, "Import_DE", "ACA"))
    assert [str(ts) for ts in df.index] == [
        "2025-10-26 01:45:00+02:00",
        "2025-10-26 03:00:00+01:00",
    ]
    assert list(df.net_flow) == [100.0, 600.0]


def test_exchange_normal_day_keeps_every_slot():
    df = parse_exchange_to_df(_payload("2025-06-15", "Import_DE", "ACA"))
    assert len(df) == len(PERIODES)


def test_production_spring_gap_keeps_existing_slots_only():
    df = parse_production_to_df(_payload(SPRING_DAY, "Eolien", "France"))
    assert [str(ts) for ts in df.index] == [
        "2025-03-30 01:45:00+01:00",
        "2025-03-30 03:00:00+02:00",
    ]
