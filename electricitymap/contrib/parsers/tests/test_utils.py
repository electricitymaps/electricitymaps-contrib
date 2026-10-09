import re
from datetime import datetime, timedelta, timezone
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time

import electricitymap.contrib.parsers.lib.utils as tested


def test_TOKEN_WIKI_URL():
    assert (
        tested.TOKEN_WIKI_URL
        == "https://github.com/electricitymaps/electricitymaps-contrib/wiki/Create-tokens"
    )


def test_get_token():
    with mock.patch.dict(
        "electricitymap.contrib.parsers.lib.utils.os.environ", {"token": "42"}
    ):
        assert tested.get_token("token") == "42"

    with (
        mock.patch.dict("electricitymap.contrib.parsers.lib.utils.os.environ", {}),
        pytest.raises(Exception, match=re.escape(tested.TOKEN_WIKI_URL)),
    ):
        tested.get_token("token")

    with (
        mock.patch.dict(
            "electricitymap.contrib.parsers.lib.utils.os.environ", {"token": ""}
        ),
        pytest.raises(Exception, match=re.escape(tested.TOKEN_WIKI_URL)),
    ):
        tested.get_token("token")


@freeze_time("2026-10-01 12:34:56")
def test_to_utc_none_is_now_in_utc():
    assert tested.to_utc(None) == datetime(2026, 10, 1, 12, 34, 56, tzinfo=timezone.utc)
    assert tested.to_utc(None).utcoffset() == timedelta(0)


def test_to_utc_naive_is_assumed_utc():
    assert tested.to_utc(datetime(2026, 9, 30, 22, 30)) == datetime(
        2026, 9, 30, 22, 30, tzinfo=timezone.utc
    )
    assert tested.to_utc(datetime(2026, 9, 30, 22, 30)).tzinfo == timezone.utc


def test_to_utc_converts_aware_values():
    converted = tested.to_utc(datetime(2026, 10, 1, 0, 30, tzinfo=ZoneInfo("CET")))
    assert converted == datetime(2026, 9, 30, 22, 30, tzinfo=timezone.utc)
    assert converted.tzinfo == timezone.utc
