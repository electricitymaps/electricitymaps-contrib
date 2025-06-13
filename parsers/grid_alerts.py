import datetime
import json

import requests
from requests.auth import HTTPBasicAuth

# CONFIGURATION
MAILGUN_API_KEY = "key-1635ecb784cc83a48f1cf4dc4bb311e8"  # Replace with your actual Mailgun private API key
REGION = "eu"  # use 'us' or 'eu'
API_BASE_URL = f"https://api.{REGION}.mailgun.net/v1/analytics/logs"
# REQUEST BODY

nowminus5 = (
    datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    - datetime.timedelta(hours=5)
).strftime("%a, %d %b %Y %H:%M:%S -0000")

now = (
    datetime.datetime.now(datetime.timezone.utc)
    .replace(microsecond=0)
    .strftime("%a, %d %b %Y %H:%M:%S -0000")
)

payload = {
    "start": nowminus5,
    "end": now,
    "filter": {
        "AND": [
            {
                "attribute": "domain",
                "comparator": "=",
                "values": [
                    {
                        "label": "alerts.electricitymaps.com",
                        "value": "alerts.electricitymaps.com",
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
    "events": ["stored", "delivered", "accepted"],  # Add or change based on your needs
    "include_subaccounts": True,
    "include_totals": True,
    "pagination": {
        "sort": "timestamp:asc",
        "limit": 100,
        # "token": "your-pagination-token"  # Optional for next pages
    },
}
# MAKE REQUEST
response = requests.post(
    API_BASE_URL,
    auth=HTTPBasicAuth("api", MAILGUN_API_KEY),
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload),
)

# get storage keys
keys = []
if response.status_code == 200:
    logs = response.json()
    print("Logs fetched successfully.\n")
    for log in logs.get("items", []):
        print(log["storage"]["key"])
        keys.append(log["storage"]["key"])
    if logs.get("pagination", {}).get("next"):
        print("\n:repeat: Next page token:", logs["pagination"]["next"]["token"])
else:
    print("Error:", response.status_code, response.text)


# get email using storage keys
for storage_key in keys:
    domain_name = "alerts.electricitymaps.com"

    API_BASE_URL2 = f"https://api.{REGION}.mailgun.net/v3/domains/{domain_name}/messages/{storage_key}"

    # MAKE REQUEST
    response = requests.get(
        API_BASE_URL2,
        auth=HTTPBasicAuth("api", MAILGUN_API_KEY),
        headers={"Content-Type": "application/json"},
    )
    print(response.json())
