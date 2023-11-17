from datetime import datetime


def get_capacity_data(capacity_config: dict, dt: datetime) -> dict[str, float]:
    """Gets the capacity data for a given zone and datetime from ZONES_CONFIG."""
    capacity = {}
    for mode, capacity_value in capacity_config.items():
        if isinstance(capacity_value, (int, float)):
            # TODO: This part is used for the old capacity format. It shoud be removed once all capacity configs are updated
            capacity[mode] = capacity_value
        else:
            capacity[mode] = get_capacity_value_with_datetime(capacity_value, dt)
    return capacity


def get_capacity_value_with_datetime(
    mode_capacity: list | dict, dt: datetime
) -> float | None:
    capacity = None
    if isinstance(mode_capacity, dict):
        capacity = mode_capacity["value"]
    elif isinstance(mode_capacity, list):
        datetime_keys = sorted(
            [datetime.fromisoformat(d["datetime"]) for d in mode_capacity]
        )

        if dt <= min(datetime_keys):
            capacity_dt = min(datetime_keys)
        else:
            # valid datetime is the min of the 2 datetime_keys surrounding dt
            capacity_dt = max([d for d in datetime_keys if d <= dt])

        capacity = [
            d["value"]
            for d in mode_capacity
            if d["datetime"] == capacity_dt.strftime("%Y-%m-%d")
        ][0]
    return capacity
