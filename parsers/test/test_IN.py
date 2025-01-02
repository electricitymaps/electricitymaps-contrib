from datetime import datetime

from parsers.IN import get_start_of_day


def test_get_start_of_day():
    start_day = get_start_of_day(datetime.fromisoformat("2020-12-16 18:30:00+00:00"))
    assert start_day == datetime.fromisoformat("2020-12-17 00:00:00+05:30")

    start_day = get_start_of_day(datetime.fromisoformat("2020-12-16 18:29:00+00:00"))
    assert start_day == datetime.fromisoformat("2020-12-16 00:00:00+05:30")

    start_day = get_start_of_day(datetime.fromisoformat("2020-12-17 00:00:00+00:00"))
    assert start_day == datetime.fromisoformat("2020-12-17 00:00:00+05:30")
