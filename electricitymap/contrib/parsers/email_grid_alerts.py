"""Parser from email alerts sent to grid-alerts@alerts.electricitymaps.com through the Mailgun API."""

import datetime
import json
from logging import Logger, getLogger
from typing import Any

from requests import Session
from requests.auth import HTTPBasicAuth

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import GridAlertList
from electricitymap.contrib.lib.models.events import GridAlertType
from electricitymap.contrib.parsers.lib.utils import get_token

# CONFIGURATION
REGION = "eu"  # use 'us' or 'eu'
API_BASE_URL = f"https://api.{REGION}.mailgun.net/v1/analytics/logs"


def fetch_grid_alerts_emails(
    zone_key: ZoneKey = None,
    session: Session | None = None,
    target_datetime: datetime.datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = session or Session()
    MAILGUN_API_KEY = get_token("MAILGUN_TOKEN")

    domain_name = "alerts.electricitymaps.com"
    # REQUEST BODY: only implemented for the last 5 hours
    nowminus5hours = (
        datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        - datetime.timedelta(hours=5)
    ).strftime("%a, %d %b %Y %H:%M:%S -0000")

    now = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .strftime("%a, %d %b %Y %H:%M:%S -0000")
    )

    # Prepare the payload for the API request
    payload = {
        "start": nowminus5hours,
        "end": now,
        "filter": {
            "AND": [
                {
                    "attribute": "domain",
                    "comparator": "=",
                    "values": [
                        {
                            "label": domain_name,
                            "value": domain_name,
                        }
                    ],
                },
                {
                    "attribute": "event",
                    "comparator": "=",
                    "values": [{"label": "stored", "value": "stored"}],
                },
            ],
        },
        "events": [
            "stored",
            "delivered",
            "accepted",
        ],  # Add or change based on your needs
        "include_subaccounts": True,
        "include_totals": True,
        "pagination": {
            "sort": "timestamp:asc",
            "limit": 100,
            # "token": "your-pagination-token"  # Optional for next pages
        },
    }

    # MAKE REQUEST
    response = session.post(
        API_BASE_URL,
        auth=HTTPBasicAuth("api", MAILGUN_API_KEY),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )

    # Get storage keys
    keys = []
    if response.status_code == 200:
        logs = response.json()
        for log in logs.get("items", []):
            keys.append(log["storage"]["key"])
        if logs.get("pagination", {}).get("next"):
            print("\n:repeat: Next page token:", logs["pagination"]["next"]["token"])
    else:
        print("Error:", response.status_code, response.text)

    # Record events in grid_alert_list
    grid_alert_list = GridAlertList(logger)

    # Get email using storage keys # The email is stored only for a few days (less than 3 days)
    for storage_key in keys:
        API_BASE_URL2 = f"https://api.{REGION}.mailgun.net/v3/domains/{domain_name}/messages/{storage_key}"

        # MAKE REQUEST
        response = session.get(
            API_BASE_URL2,
            auth=HTTPBasicAuth("api", MAILGUN_API_KEY),
            headers={"Content-Type": "application/json"},
        )

        # Parse email
        email_json = response.json()

        date_str = email_json["Date"].replace(" (UTC)", "")
        dt_received = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        sender = email_json["From"].lower()

        # Extract zone key from sender
        if (
            ("ercot" in sender and zone_key == ZoneKey("US-TEX-ERCO"))
            or ("flexalert" in sender and zone_key == ZoneKey("US-CAL-CISO"))
            or ("spp" in sender and zone_key == ZoneKey("US-CENT-SWPP"))
            or ("electricitymaps" in sender)
        ):
            body = ""
            if ZoneKey("US-CENT-SWPP") == zone_key:
                body = email_json["body-plain"].split(
                    "The following chart shows the relative severity of"
                )[0]
            # add more cases when we know the format of the other emails

            message = email_json["subject"] + "\n" + body
            # Add to grid_alert_list
            grid_alert_list.append(
                zoneKey=zone_key,
                locationRegion=None,
                source=sender,
                alertType=GridAlertType.undefined,
                message=message,
                issuedTime=dt_received,
                startTime=None,  # if None, it defaults to issuedTime
                endTime=None,
            )
        else:
            logger.warning(f"Unknown sender: {email_json['sender']}")

    return grid_alert_list.to_list()


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_grid_alerts_emails())
