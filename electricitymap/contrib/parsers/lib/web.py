from bs4 import BeautifulSoup
from requests import Response, Session

from .exceptions import ParserException


def get_response(zone_key: str, url: str, session: Session | None = None):
    ses = session or Session()
    response: Response = ses.get(url)
    if response.status_code != 200:
        raise ParserException(zone_key, f"Response code: {response.status_code}")
    return response


def get_response_with_params(
    zone_key: str, url, session: Session | None = None, params=None
):
    ses = session or Session()
    response: Response = ses.get(url, params=params)
    if response.status_code != 200:
        raise ParserException(zone_key, f"Response code: {response.status_code}")
    return response


def get_response_text(zone_key: str, url, session: Session | None = None):
    response = get_response(zone_key, url, session)
    if not response.text:
        raise ParserException(zone_key, "Response empty")
    return response.text


def get_response_soup(zone_key: str, url, session: Session | None = None):
    response_text = get_response_text(zone_key, url, session)
    return BeautifulSoup(response_text, "html.parser")
