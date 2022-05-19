import logging

import arrow
import cv2
import numpy as np
import pytesseract
from imageio import imread
from PIL import Image, ImageOps

url = "https://mahasldc.in/wp-content/reports/sldc/mvrreport3.jpg"

# specifies locations of data in the image
# (x,y,x,y) = upper left, lower right corner of rectangle
locations = {
    "MS WIND": {"label": (595, 934, 692, 961), "value": (785, 934, 844, 934 + 25)},
    "SOLAR TTL": {"label": (592, 577, 715, 605), "value": (772, 578, 814, 578 + 25)},
    "MS SOLAR": {"label": (595, 963, 705, 984), "value": (785, 955, 848, 955 + 25)},
    "THERMAL": {"label": (407, 982, 502, 1004), "value": (516, 987, 581, 987 + 25)},
    "GAS": {"label": (403, 1033, 493, 1056), "value": (515, 1042, 582, 1042 + 25)},
    "HYDRO": {"label": (589, 472, 666, 496), "value": (753, 468, 813, 468 + 25)},
    "TPC HYD.": {"label": (926, 525, 1035, 554), "value": (1105, 524, 1173, 524 + 25)},
    "TPC THM.": {"label": (924, 578, 1030, 604), "value": (1088, 581, 1173, 581 + 25)},
    "OTHR+SMHYD": {
        "label": (594, 1009, 730, 1031),
        "value": (789, 1009, 846, 1009 + 25),
    },
    "COGEN": {"label": (594, 989, 670, 1011), "value": (789, 982, 844, 982 + 25)},
    "AEML GEN.": {"label": (922, 687, 1041, 716), "value": (1081, 692, 1175, 692 + 25)},
    "CS GEN. TTL.": {
        "label": (1341, 998, 1492, 1029),
        "value": (1549, 1000, 1616, 1000 + 25),
    },
    "KK’ PARA": {"label": (1346, 708, 1457, 730), "value": (1560, 707, 1626, 707 + 25)},
    "TARPR PH-I": {
        "label": (1341, 730, 1484, 757),
        "value": (1556, 733, 1626, 733 + 25),
    },
    "TARPR PH-II": {
        "label": (1341, 750, 1490, 782),
        "value": (1556, 757, 1626, 757 + 25),
    },
    "SSP": {"label": (1341, 800, 1401, 823), "value": (1557, 802, 1626, 802 + 25)},
    "RGPPL": {"label": (1343, 822, 1421, 849), "value": (1560, 823, 1620, 823 + 25)},
    "GANDHAR": {"label": (1341, 660, 1446, 689), "value": (1562, 661, 1623, 661 + 25)},
    "CS EXCH": {"label": (920, 303, 1021, 338), "value": (1090, 309, 1172, 309 + 25)},
    # STATE DEMAND (including Mumbai!)
    "DEMAND": {"label": (932, 1003, 1021, 1030), "value": (1080, 996, 1167, 996 + 25)},
    # RE TTL
    "TTL": {"label": (597, 1035, 663, 1056), "value": (784, 1032, 845, 1032 + 25)},
    "TTL (IPP/CPP+RE)": {
        "label": (594, 1072, 765, 1098),
        "value": (786, 1068, 849, 1068 + 25),
    },
    "PIONEER": {"label": (592, 910, 694, 929), "value": (814, 906, 844, 906 + 25)},
}

generation_map = {
    "biomass": {"add": ["COGEN"], "subtract": []},
    "coal": {
        "add": [
            "THERMAL",
            "TTL (IPP/CPP+RE)",
            "TPC THM.",
            "CS GEN. TTL.",
            "AEML GEN.",
            "SOLAR TTL",
        ],
        "subtract": [
            "TTL",
            "PIONEER",
            "SSP",
            "RGPPL",
            "TARPR PH-I",
            "TARPR PH-II",
            "KK’ PARA",
            "GANDHAR",
        ],
    },
    "gas": {"add": ["GAS", "PIONEER", "GANDHAR", "RGPPL"], "subtract": []},
    "hydro": {"add": ["HYDRO", "TPC HYD.", "SSP"], "subtract": []},
    "nuclear": {"add": ["TARPR PH-I", "TARPR PH-II", "KK’ PARA"], "subtract": []},
    "solar": {"add": ["MS SOLAR"], "subtract": []},
    "wind": {"add": ["MS WIND"], "subtract": []},
    "unknown": {"add": ["OTHR+SMHYD"], "subtract": []},
}

# list of values that belong to Central State production
CS = [
    "SSP",
    "RGPPL",
    "TARPR PH-I",
    "TARPR PH-II",
    "KK’ PARA",
    "GANDHAR",
    "CS GEN. TTL.",
]

# converts image into a black and white
def RGBtoBW(pil_image):
    # pylint: disable=no-member
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return Image.fromarray(image)


# returns image section
def read(location, source):
    img = source.crop(location)
    img = RGBtoBW(img)
    img = ImageOps.invert(img)
    return img


# TODO: this function actually fetches consumption data
def fetch_production(
    zone_key="IN-MH",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:

    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    dt = arrow.now("Asia/Kolkata").floor("minute").datetime

    data = {
        "zoneKey": "IN-MH",
        "datetime": dt,
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "nuclear": 0.0,
            "solar": 0.0,
            "wind": 0.0,
            "unknown": 0.0,
        },
        "storage": {},
        "source": "mahasldc.in",
    }

    image = imread(url)
    image = Image.fromarray(image)  # create PIL image

    imgs = [read(loc["value"], image) for loc in locations.values()]

    # string together all image sections and recognize resulting line
    imgs_line = np.hstack(list(np.asarray(i) for i in imgs[:]))
    imgs_line = Image.fromarray(imgs_line)
    text = pytesseract.image_to_string(imgs_line, lang="digits_comma", config="--psm 7")
    text = text.split(" ")

    # generate dict from string list
    values = {}
    for count, key in enumerate(locations):
        values[key] = max([float(text[count]), 0])

    # fraction of central state production that is exchanged with Maharashtra
    share = values["CS EXCH"] / values["CS GEN. TTL."]

    for type, plants in generation_map.items():
        for plant in plants["add"]:
            fac = (
                share if plant in CS else 1
            )  # add only a fraction of central state plant consumption
            data["production"][type] += fac * values[plant]
        for plant in plants["subtract"]:
            fac = share if plant in CS else 1
            data["production"][type] -= fac * values[plant]

    # Sum over all production types is expected to equal the total demand
    demand_diff = sum(data["production"].values()) - values["DEMAND"]
    assert (
        abs(demand_diff) < 30
    ), "Production types do not add up to total demand. Difference: {}".format(
        demand_diff
    )

    return data


if __name__ == "__main__":

    print(fetch_production())
