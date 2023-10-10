#!/usr/bin/env python3
import re
from datetime import datetime
from io import BytesIO
from logging import Logger, getLogger
from typing import Optional
import pytz
from urllib.request import Request, urlopen

# The arrow library is used to handle datetimes
import arrow
from bs4 import BeautifulSoup
from PIL import Image
from pytesseract import image_to_string

# The request library is used to fetch content through HTTP
from requests import Session

from .JP import fetch_production as JP_fetch_production

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(
    zone_key: str = "JP-SK",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    breakpoint()
    """
    This method adds nuclear production on top of the solar data returned by the JP parser.
    It tries to match the solar + unknown data with the nuclear data.
    """
    r = session or Session()
    if target_datetime is not None:
        raise NotImplementedError("This parser can only fetch live data")
    # fetch data from TSO - unknown + solar
    JP_data = JP_fetch_production(zone_key, session, target_datetime, logger)
    # we fetch the latest data point from the JP parser
    latest_data_point_JP_SK = JP_data[-1]
    # Fetch nuclear data from the nuclear power plant website
    ## fetch image url
    image_url = get_nuclear_power_image_url(URL, session)
    ## fetch nuclear power from image url
    nuclear_power_MW, datetime_nuclear = get_nuclear_power_from_image_url(image_url, session)
    breakpoint()
    # TODO - Check if the datetime of the nuclear data is close to the solar data


    latest_data_point_JP_SK["production"]["nuclear"] = nuclear_power_MW

    return latest_data_point_JP_SK


URL = "https://www.yonden.co.jp/energy/atom/ikata/ikt722.html"
IMAGE_CORE_URL = "https://www.yonden.co.jp/energy/atom/ikata/"


def get_nuclear_power_image_url(url, session) -> (datetime, float):
    # TODO: extract production value from image on TOP
    session = Session()
    response_main_page = session.get(URL)
    # breakpoint()
    soup = BeautifulSoup(response_main_page.content, "html.parser")
    images_links = soup.find_all("img", src=True)
    filtered_img_tags = [
        tag for tag in images_links if tag["src"].startswith("ikt721-1")
    ]
    if len(filtered_img_tags) == 0:
        raise Exception("No image found")
    img_url = IMAGE_CORE_URL + filtered_img_tags[0]["src"]
    # breakpoint()
    return img_url


def get_nuclear_power_from_image_url(img_url, session):
    session = Session()
    response_image = session.get(img_url)
    image = Image.open(BytesIO(response_image.content))
    width, height = image.size
    img = image.crop((0, 0, width, height))
    # image.save("test.png")
    breakpoint()
    text = image_to_string(img)
    numeric_pattern = r"\d+"
    # this method extracts the second number from the image since it is the nuclear power value from the image
    # in case the image format changes, this method will need to be updated
    nuclear_power = float(re.findall(numeric_pattern, text)[1])
    # extract timestamp from image_url and convert it to datetime
    timestamp_pattern = r"\d{12}"
    timestamp = re.findall(timestamp_pattern, img_url)[0]
    # convert timestamp to datetime
    # TODO - include tzone
    datetime_nuclear = datetime.strptime(timestamp, "%Y%m%d%H%M").replace(tzinfo=pytz.timezone('Asia/Tokyo'))
    # datetime_nuclear.astimezone(pytz.timezone('Asia/Tokyo'))
    breakpoint()
    # datetime_nuclear = datetime_nuclear.replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=9)))
    return nuclear_power, datetime_nuclear


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
