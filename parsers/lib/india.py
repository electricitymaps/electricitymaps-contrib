from arrow import get


def read_datetime_from_span_id(html, span_id, format):
    """Read date time from span with id"""
    date_time_span = html.find('span', {'id': span_id})
    india_date_time = date_time_span.text + ' Asia/Kolkata'
    return get(india_date_time, format + ' ZZZ')


def read_value_from_span_id(html, span_id):
    """Read value from span with id"""
    html_span = html.find('span', {'id': span_id})
    return float(html_span.text)

