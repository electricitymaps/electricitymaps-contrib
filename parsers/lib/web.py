from http import HTTPStatus
from typing import Optional

from bs4 import BeautifulSoup
from requests import Response, Session

from .exceptions import ParserException


def get_response(zone_key: str, url: str, session: Optional[Session] = None):
    ses = session or Session()
    response: Response = ses.get(url)
    if response.status_code != HTTPStatus.OK:
        raise ParserException(
            zone_key, "Response code: {0}".format(response.status_code)
        )
    return response


def get_response_with_params(
    zone_key: str, url, session: Optional[Session] = None, params=None
):
    ses = session or Session()
    response: Response = ses.get(url, params=params)
    if response.status_code != HTTPStatus.OK:
        raise ParserException(
            zone_key, "Response code: {0}".format(response.status_code)
        )
    return response


def get_response_text(zone_key: str, url, session: Optional[Session] = None):
    response = get_response(zone_key, url, session)
    if not response.text:
        raise ParserException(zone_key, "Response empty")
    return response.text


def get_response_soup(zone_key: str, url, session: Optional[Session] = None):
    response_text = get_response_text(zone_key, url, session)
    return BeautifulSoup(response_text, "html.parser")


def post_request(
    zone_key: str, url, data=None, json=None, session: Optional[Session] = None
):
    ses = session or Session()
    response: Response = ses.post(url, data=data, json=json)
    if response.status_code != HTTPStatus.OK:
        raise ParserException(
            zone_key,
            f"Response status code: {response.status_code} reason: {response.reason}",
        )
    return response


def read_response_text(zone_key: str, response: Response):
    if not response.text:
        raise ParserException(zone_key, "Response text empty")
    return response.text


def read_response_json(zone_key: str, response: Response):
    response_json = response.json()
    if not response_json:
        raise ParserException(zone_key, "Response JSON empty")
    return response_json
