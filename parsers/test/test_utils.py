from unittest import mock

import pytest
import requests

import parsers.lib.utils as tested


def test_TOKEN_WIKI_URL():
    assert requests.get(tested.TOKEN_WIKI_URL).status_code == 200


def test_get_token():
    with mock.patch.dict("parsers.lib.utils.os.environ", {"token": "42"}):
        assert tested.get_token("token") == "42"

    with (
        mock.patch.dict("parsers.lib.utils.os.environ", {}),
        pytest.raises(Exception),
    ):
        tested.get_token("token")

    with (
        mock.patch.dict("parsers.lib.utils.os.environ", {"token": ""}),
        pytest.raises(Exception),
    ):
        tested.get_token("token")
