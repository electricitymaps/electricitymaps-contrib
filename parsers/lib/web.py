from requests import Session
from bs4 import BeautifulSoup

from parsers.lib.exceptions import ParserException


def get_response(country_code, url, session=None):
    """Get response"""
    ses = session or Session()
    response = ses.get(url)
    if response.status_code != 200:
        raise ParserException(country_code, 'Response code: {0}'.format(response.status_code))
    return response


def get_response_text(country_code, url, session=None):
    """Get text response"""
    response = get_response(country_code, url, session)
    if not response.text:
        raise ParserException(country_code, 'Response empty')
    return response.text


def get_response_soup(country_code, url, session=None):
    """Get BeautifulSoup response"""
    response_text = get_response_text(country_code, url, session)
    return BeautifulSoup(response_text, 'html.parser')
