import json
import os
import pandas as pd
import requests
import threading
import datetime 

from io import StringIO


APG_API_BASE="https://transparency.apg.at/transparency-api/api/v1"
EXCHANGE_API="{}/Download/CBPF/German/M15".format(APG_API_BASE)

# column names
COL_FROM="Zeit von [CET/CEST]"
COL_TO="Zeit bis [CET/CEST]"
COL_CZ_AT="CZ>AT Leistung [MW]"
COL_HU_AT="HU>AT Leistung [MW]"
COL_SI_AT="SI>AT Leistung [MW]"
COL_IT_AT="IT>AT Leistung [MW]"
COL_CH_AT="CH>AT Leistung [MW]"
COL_DE_AT="DE>AT Leistung [MW]"
EXCHANGE_COLS = [COL_CZ_AT, COL_HU_AT, COL_SI_AT, COL_IT_AT, COL_CH_AT, COL_DE_AT]


def format_date(date):
    return "{}T000000".format(date.isoformat())


def fetch_exchange_data(date=None):
    if date is None:
        date = datetime.date.today()

    from_date = format_date(date)
    to_date = format_date(date + datetime.timedelta(days=1))

    export_request_url = "{}/{}/{}".format(EXCHANGE_API, from_date, to_date)
    resp = requests.get(export_request_url)
    resp.raise_for_status()

    try:
        export_url_response = resp.json()["ResponseData"]
        cache_id = export_url_response["Cache_ID"]
        filename = export_url_response["FileName"]
    except:
        raise ValueError("The response to the request for generating the csv file has an unexpected format.")

    csv_url = "{}/{}/{}".format(export_request_url, cache_id, filename)
    csv_response = requests.get(csv_url)
    csv_response.raise_for_status()

    # override encoding by real educated guess as provided by chardet
    csv_response.encoding = csv_response.apparent_encoding
    csv_str = csv_response.text

    try:
        csv_data = pd.read_csv(StringIO(csv_str), delimiter=";", parse_dates=[COL_FROM, COL_TO], dayfirst=True)
    except:
        raise ValueError("The downloaded csv file has an unexpected format")

    # parse float values
    csv_data[EXCHANGE_COLS] = csv_data[EXCHANGE_COLS].replace(to_replace=",", value='.', regex=True).apply(pd.to_numeric)
        
    return csv_data


def check_delay():
    threading.Timer(60.0, check_delay).start() # called every minute

    exchange_data = fetch_exchange_data()

    last_row = exchange_data.dropna().iloc[-1]
    end_date = last_row[COL_TO]

    if end_date.isoformat() not in STORAGE:
        delta = datetime.datetime.now() - end_date
        last_row["Delay [Minutes]"] = delta.seconds / 60
        STORAGE[end_date.isoformat()] = last_row.astype(str).to_dict()
        print("Encountered new exchange data with delay {}".format(delta))
    else:
       print("No new data is available")

    with open(STORAGE_FILE, "w") as f:
        json.dump(STORAGE, f)


STORAGE = {}
STORAGE_FILE = "delay_storage.json"


def main():
    if os.path.isfile(STORAGE_FILE):
        with open(STORAGE_FILE) as f:
            STORAGE = json.load(f) 

    check_delay()


if __name__ == "__main__":
    main()