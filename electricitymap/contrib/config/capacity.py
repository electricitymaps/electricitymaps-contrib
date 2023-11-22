from datetime import datetime


def get_capacity_data(capacity_config: dict, dt: datetime) -> dict[str, float]:
    """Gets the capacity data for a given zone and datetime from ZONES_CONFIG."""
    capacity = {}
    for mode, capacity_value in capacity_config.items():
        if isinstance(capacity_value, int | float):
            # TODO: This part is used for the old capacity format. It shoud be removed once all capacity configs are updated
            capacity[mode] = capacity_value
        else:
            capacity[mode] = get_capacity_value_with_datetime(capacity_value, dt)
    return capacity


def get_capacity_value_with_datetime(
    mode_capacity: list | dict, dt: datetime
) -> float | None:
    if isinstance(mode_capacity, dict):
        return mode_capacity["value"]
    elif isinstance(mode_capacity, list):
        capacity_tuples = [(d["datetime"], d["value"]) for d in mode_capacity]

        if dt.isoformat() <= min(capacity_tuples)[0]:
            return min(capacity_tuples)[1]
        else:
            # valid datetime is the max datetime that is lower than the given datetime
            # In other words, it is the most recent value that is valid for the given dt
            return max([(d, v) for d, v in capacity_tuples if d <= dt.isoformat()])[1]
