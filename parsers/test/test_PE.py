# from freezegun import freeze_time
from requests import Session
from requests_mock import POST, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.PE import API_ENDPOINT, fetch_production


# @freeze_time("2024-02-07 10:00:00", tz_offset=-5)
def test_production(snapshot):
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    mock_file_today = open("parsers/test/mocks/PE/response_20240206.json", "rb")
    mock_file_yesterday = open("parsers/test/mocks/PE/response_20240205.json", "rb")
    # Try to use additional matcher for request json data
    # adapter.register_uri(
    #     POST,
    #     API_ENDPOINT,
    #     content=mock_file_today.read(),
    #     additional_matcher=lambda request: request.json()
    #     # == {
    #     #     "data": {
    #     #         "fechaInicial": "07/02/2024",
    #     #         "fechaFinal": "08/02/2024",
    #     #         "indicador": 0,
    #     #     }
    #     # },
    #     == {
    #         "fechaInicial": "",
    #         "fechaFinal": "",
    #         "indicador": 0,
    #     },
    # )
    adapter.register_uri(
        POST,
        API_ENDPOINT,
        response_list=[
            {"content": mock_file_today.read()},
            {"content": mock_file_yesterday.read()},
        ],
    )

    production = fetch_production(
        zone_key=ZoneKey("PE"),
        session=session,
    )
    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "production": element["production"],
                # "storage": element["storage"],
                "source": element["source"],
                "zoneKey": element["zoneKey"],
                "sourceType": "measured",
            }
            for element in production
        ]
    )
