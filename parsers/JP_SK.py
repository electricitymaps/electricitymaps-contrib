#!/usr/bin/env python3
import re
from datetime import datetime
from io import BytesIO
from logging import Logger, getLogger
from typing import Optional
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
    It tries to match the solar data with the nuclear data.
    If there is a difference of more than 30 minutes between solar and nuclear data, the method will fail.
    """
    r = session or Session()
    if target_datetime is not None:
        raise NotImplementedError("This parser can only fetch live data")
    JP_data = JP_fetch_production(zone_key, session, target_datetime, logger)
    breakpoint()
    # TODO: add nuclear production
    nuclear_mw, nuclear_datetime = get_nuclear_from_image(zone_key)
    # TODO - Check if the datetime of the nuclear data is close to the solar data
    latest = JP_data[-1]
    latest["production"]["nuclear"] = nuclear_mw

    return latest


URL = "https://www.yonden.co.jp/energy/atom/ikata/ikt722.html"
IMAGE_CORE_URL = "https://www.yonden.co.jp/energy/atom/ikata/"


def get_nuclear_power_image_url(url, session) -> (datetime, float):
    # TODO: extract production value from image on TOP
    session = Session()
    response_main_page = session.get(URL)
    breakpoint()
    soup = BeautifulSoup(response_main_page.content, 'html.parser')
    images_links = soup.find_all('img', src=True)
    filtered_img_tags = [tag for tag in images_links if tag['src'].startswith('ikt721-1')]
    if len(filtered_img_tags) == 0:
        raise Exception("No image found")
    img_url = IMAGE_CORE_URL + filtered_img_tags[0]['src']
    breakpoint()
    return img_url

def get_nuclear_power_from_image_url(img_url, session):
    response_image = session.get(img_url)
    image = Image.open(BytesIO(response_image.content))
    width, height = image.size
    img = image.crop((0, 0, width, height))
    # image.save("test.png")
    text = image_to_string(img)
    numeric_pattern = r'\d+'
    # this method extracts the second number from the image since it is the nuclear power value from the image
    # in case the image format changes, this method will need to be updated
    nuclear_power = float(re.findall(numeric_pattern, text)[1])
    return nuclear_power



if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
