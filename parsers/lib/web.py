from requests import Session
from bs4 import BeautifulSoup


def get_response(country_code, url, session=None):
    """Get response"""
    ses = session or Session()
    response = ses.get(url)
    if not response:
        raise Exception('{0} Parser not response'.format(country_code))
    if response.status_code != 200:
        raise Exception('{0} Parser Response code: {1}'.format(country_code, response.status_code))
    return response


def get_response_text(country_code, url, session=None):
    """Get text response"""
    response = get_response(country_code, url, session)
    if not response.text:
        raise Exception('{0} Parser Response empty'.format(country_code))
    return response.text


def get_response_soup(country_code, url, session=None):
    """Get BeautifulSoup response"""
    response_text = get_response_text(country_code, url, session)
    return BeautifulSoup(response_text, 'html.parser')
