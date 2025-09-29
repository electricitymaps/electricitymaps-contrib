from datetime import datetime
from zoneinfo import ZoneInfo

ZONE_INFO = ZoneInfo("Asia/Kolkata")


def read_datetime_from_span_id(html, span_id, time_format):
    date_time_span = html.find("span", {"id": span_id})
    return datetime.strptime(date_time_span.text, time_format).replace(tzinfo=ZONE_INFO)


def read_text_from_span_id(html, span_id):
    return html.find("span", {"id": span_id}).text


def read_value_from_span_id(html, span_id):
    html_span = read_text_from_span_id(html, span_id)
    return float(html_span)
