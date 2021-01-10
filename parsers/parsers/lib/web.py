from requests import Session
from bs4 import BeautifulSoup

from .exceptions import ParserException


def get_response(zone_key, url, session=None):
    """Get response"""
    ses = session or Session()
    response = ses.get(url)
    if response.status_code != 200:
        raise ParserException(zone_key, 'Response code: {0}'.format(response.status_code))
    return response


def get_response_with_params(zone_key, url, session=None, params=None):
    """Get response"""
    ses = session or Session()
    response = ses.get(url, params= params)
    if response.status_code != 200:
        raise ParserException(zone_key, 'Response code: {0}'.format(response.status_code))
    return response


def get_response_text(zone_key, url, session=None):
    """Get text response"""
    response = get_response(zone_key, url, session)
    if not response.text:
        raise ParserException(zone_key, 'Response empty')
    return response.text


def get_response_soup(zone_key, url, session=None):
    """Get BeautifulSoup response"""
    response_text = get_response_text(zone_key, url, session)
    return BeautifulSoup(response_text, 'html.parser')
