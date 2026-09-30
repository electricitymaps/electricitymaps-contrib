import re
from unittest import mock

import pytest

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
