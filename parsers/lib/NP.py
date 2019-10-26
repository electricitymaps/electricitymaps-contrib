from arrow import get, utcnow


def read_datetime_from_span_id(html, span_id, format):
    """Read date time from span with id"""
    date_time_span = html.find('span', {'id': span_id})
    nepal_date_time = date_time_span.text + ' Asia/Kathmandu'
    return get(nepal_date_time, format + ' ZZZ')

def read_text_from_span_id(html, span_id):
    """Read text from span with id"""
    return html.find('span', {'id': span_id}).text


def read_value_from_span_id(html, span_id):
    """Read value from span with id"""
    html_span = read_text_from_span_id(html, span_id)
    return float(html_span)


def read_datetime_with_only_time(time_string, time_format, now=utcnow()):
    utc = now.floor('hour')
    nepal_now = utc.to('Asia/Kathmandu')
    time = get(time_string, time_format)
    india_date_time = nepal_now.replace(hour=time.hour, minute=time.minute, second=time.second)
    if nepal_date_time > nepal_now:
        nepal_date_time.shift(days=-1)
    return nepal_date_time
