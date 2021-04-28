#!/usr/bin/env python3

# Parser for Peninsular Malaysia (West Malaysia).
# This does not include the states of Sarawak and Sarawak.
# There is pumped storage in the Peninsular but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
from dateutil import parser
from logging import getLogger
from pytz import timezone
import requests
from xml.etree import ElementTree

fuel_mix_url = 'https://www.gso.org.my/SystemData/FuelMix.aspx'
current_gen_url = 'https://www.gso.org.my/SystemData/CurrentGen.aspx'
exchanges_url = 'https://www.gso.org.my/SystemData/TieLine.aspx'

# Exchange with Thailand made up of EGAT and HVDC ties. Singapore exchange is PLTG tie.

fuel_mapping = {
    'ST-Coal': 'coal',
    'Hydro': 'hydro',
    'CCGT-Gas': 'gas',
    'Co-Gen': 'unknown',
    'OCGT-Gas': 'gas',
    'ST-Gas': 'gas'
}


def get_data(session=None) -> tuple:
    """
    Makes two requests for the current generation total and fuel mix.
    Parses the data into raw form and reads time string associated with it.
    Checks that fuel mix sum is equal to generation total.
    """

    s = session or requests.Session()
    mixreq = s.get(fuel_mix_url)
    genreq = s.get(current_gen_url)
    mixsoup = BeautifulSoup(mixreq.content, 'html.parser')
    gensoup = BeautifulSoup(genreq.content, 'html.parser')

    try:
        gen_mw = gensoup.find('td', text="MW")
        ts_tag = gen_mw.findNext('td')
        real_ts = ts_tag.text
        gen_total = float(ts_tag.findNext('td').text)

    except AttributeError:
        # No data is available between 12am-1am.
        raise ValueError('No production data is currently available for West Malaysia.')

    mix_header = mixsoup.find('tr', {"class": "gridheader"})
    mix_table = mix_header.find_parent("table")
    rows = mix_table.find_all('tr')
    generation_mix = {}
    for row in rows[1:]:
        cells = row.find_all('td')
        items = [ele.text.strip() for ele in cells]
        generation_mix[items[0]] = float(items[1])

    if sum(generation_mix.values()) == gen_total:
        # Fuel mix matches generation.
        return real_ts, generation_mix
    else:
        raise ValueError('Malaysia generation and fuel mix totals are not equal!')


def convert_time_str(ts):
    """Converts a unicode time string into an aware datetime object."""

    dt_naive = datetime.datetime.strptime(ts, '%m/%d/%Y %I:%M:%S %p')
    localtz = timezone('Asia/Kuala_Lumpur')
    dt_aware = localtz.localize(dt_naive)

    return dt_aware


def data_processer(rawdata, logger) -> tuple:
    """Takes in raw data and converts it into a usable form."""

    converted_time_string = convert_time_str(rawdata[0])

    current_generation = rawdata[1]

    unmapped = []
    for gen_type in current_generation.keys():
        if gen_type not in fuel_mapping.keys():
            unmapped.append(gen_type)

    mapped_generation = [(fuel_mapping.get(gen_type, 'unknown'), val) for gen_type, val in
                         current_generation.items()]

    generationDict = defaultdict(lambda: 0.0)

    # Sum values for duplicate keys.
    for key, val in mapped_generation:
        generationDict[key] += val

    for key in ['solar', 'wind']:
        generationDict[key] = None

    for key in ['nuclear', 'geothermal']:
        generationDict[key] = 0.0

    for gen_type in unmapped:
        logger.warning('{} is missing from the MY generation type mapping!'.format(gen_type))

    return converted_time_string, dict(generationDict)


def fetch_production(zone_key='MY-WM', session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_data = get_data(session=None)
    clean_data = data_processer(raw_data, logger)

    production = {
        'zoneKey': zone_key,
        'datetime': clean_data[0],
        'production': clean_data[1],
        'storage': {
            'hydro': None,
        },
        'source': 'gso.org.my'
    }

    return production


def extract_hidden_values(req) -> dict:
    """Gets current aspx page values to enable post requests to be sent."""

    soup = BeautifulSoup(req.content, 'html.parser')

    # Find and define parameters needed to send a POST request.
    try:
        viewstategenerator = soup.find("input", attrs={'id': '__VIEWSTATEGENERATOR'})['value']
        viewstate = soup.find("input", attrs={'id': '__VIEWSTATE'})['value']
        eventvalidation = soup.find("input", attrs={'id': '__EVENTVALIDATION'})['value']
        jschartviewerstate = soup.find("input", attrs={'id': 'MainContent_ctl17_JsChartViewerState'})['value']
    except TypeError:
        raise ValueError('No exchange data is currently available for West Malaysia.')

    hidden_values = {'viewstategenerator': viewstategenerator,
                     'viewstate': viewstate,
                     'eventvalidation': eventvalidation,
                     'jschartviewerstate': jschartviewerstate}

    return hidden_values


def xml_processor(text) -> list:
    """
    Creates xml element tree from response.text object.
    Returns a list of tuples in the form (datetime, float).
    """

    raw_data = ElementTree.fromstring(text)

    datapoints = []
    for child in raw_data.findall('DataTable'):
        ts= child.find('Tarikhmasa').text
        val = child.find('MW').text
        dt = parser.parse(ts)
        flow = float(val)
        datapoints.append((dt, flow))

    return datapoints


def post_to_switch(tie, session):
    """
    Makes a post request to switch exchange tie shown on aspx page.
    This is required before xml data can be extracted.
    Returns a response object.
    """

    req = session.get(exchanges_url)
    hidden_values = extract_hidden_values(req)

    headers = {"Content-Type":	"application/x-www-form-urlencoded"}

    switch_tie = {'__VIEWSTATE': hidden_values['viewstate'],
                  '__VIEWSTATEGENERATOR': hidden_values['viewstategenerator'],
                  '__EVENTVALIDATION': hidden_values['eventvalidation'],
                  'ctl00$MainContent$ctl12': tie,
                  'MainContent_ctl17_callBackURL': '/SystemData/TieLine.aspx?cdLoopBack=1',
                  'MainContent_ctl17_JsChartViewerState': hidden_values['jschartviewerstate'],
                  'ctl00$MainContent$Plot': 'Plot'
                  }

    switch_req = session.post(exchanges_url, headers=headers, data=switch_tie)

    return switch_req


def post_to_extract(tie, hidden_values, session):
    """
    Makes a post request to retrieve xml data from aspx page.
    Returns a response.text object.
    """

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    postdata = {'__VIEWSTATE': hidden_values['viewstate'],
                '__VIEWSTATEGENERATOR': hidden_values['viewstategenerator'],
                '__EVENTVALIDATION': hidden_values['eventvalidation'],
                'ctl00$MainContent$ctl12': tie,
                'MainContent_ctl17_callBackURL': '/SystemData/TieLine.aspx?cdLoopBack=1',
                'MainContent_ctl17_JsChartViewerState': hidden_values['jschartviewerstate'],
                'ctl00$MainContent$ctl21.x': 10,
                'ctl00$MainContent$ctl21.y': 7
                }

    req = session.post(exchanges_url, headers=headers, data=postdata)

    return req.text


def zip_and_merge(egat_data, hvdc_data, logger) -> list:
    """
    Joins the EGAT and HVDC ties that form the MY-WM->TH exchange.
    Returns a list of tuples in the form (datetime, float).
    """

    merged_data = zip(egat_data, hvdc_data)

    mismatch_count = 0
    simplified_data = []
    for item in merged_data:
        if item[0][0] == item[1][0]:
            # Make sure datetimes are equal.
            combined = item[0][0], sum([item[0][1], item[1][1]])
            simplified_data.append(combined)
        else:
            # avoid producing excess warnings
            mismatch_count += 1
            continue

    if mismatch_count > 0:
        logger.warning('{} date mismatches between EGAT and HVDC ties found for MY-WM->TH, skipped datapoints.'.format(mismatch_count), extra={'key': 'MY-WM'})

    return simplified_data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=getLogger(__name__)) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    s=session or requests.Session()
    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))

    if sortedcodes == 'MY-WM->TH':
        # Get the EGAT data.
        req = s.get(exchanges_url)
        egat_hidden_values = extract_hidden_values(req)
        egat_data = post_to_extract('EGAT', egat_hidden_values, s)

        # Switch to HVDC and get data.
        hvdc_switch_req = post_to_switch('HVDC', s)
        hvdc_hidden_values = extract_hidden_values(hvdc_switch_req)
        hvdc_data = post_to_extract('HVDC', hvdc_hidden_values, s)

        processed_egat = xml_processor(egat_data)
        processed_hvdc = xml_processor(hvdc_data)

        data = zip_and_merge(processed_egat, processed_hvdc, logger)
    elif sortedcodes == 'MY-WM->SG':
        req = s.get(exchanges_url)
        pltg_switch_req = post_to_switch('PLTG', s)

        pltg_hidden_values = extract_hidden_values(pltg_switch_req)
        pltg_data = post_to_extract('PLTG', pltg_hidden_values, s)
        data = xml_processor(pltg_data)
    else:
        raise NotImplementedError('The exchange {} is not implemented'.format(sortedcodes))

    exchange_data = []
    for datapoint in data:
        exchange = {
            'sortedZoneKeys': sortedcodes,
            'datetime': datapoint[0],
            'netFlow': datapoint[1],
            'source': 'gso.org.my'
        }
        exchange_data.append(exchange)

    return exchange_data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(MY-WM, TH)')
    print(fetch_exchange('MY-WM', 'TH'))
    print('fetch_exchange(MY-WM, SG)')
    print(fetch_exchange('MY-WM', 'SG'))
