from PIL import Image, ImageOps
import pytesseract
import cv2
from imageio import imread
import numpy as np
import arrow
import logging

url = 'https://mahasldc.in/wp-content/reports/sldc/mvrreport3.jpg'

# specifies locations of data in the image
# (x,y,x,y) = upper left, lower right corner of rectangle
locations = {
    'MS WIND' : {
        'label' : (595,934,692,961),
        'value' : (785,934,844,959)
    },
    'MS SOLAR' : {
            'label' : (595,963,705,984),
            'value' : (785,959,848,983)
    },
    'THERMAL' : {
            'label' : (407,982,502,1004),
            'value' : (516,987,584,1015)
    },
    'GAS' : {
            'label' : (403,1033,493,1056),
            'value' : (515,1038,582,1068)
    },
    'HYDRO' : {
            'label' : (589,472,666,496),
            'value' : (753,472,817,494)
    },
    'TPC HYD.' : {
            'label' : (926,525,1035,554),
            'value' : (1100,527,1173,551)
    },
    'TPC THM.' : {
            'label' : (924,578,1030,604),
            'value' : (1088,581,1173,605)
    },
    'COGEN' : {
            'label' : (594,989,670,1011),
            'value' : (789,982,844,1007)
    },
    'OTHR+SMHYD' : {
            'label' : (594,1009,730,1031),
            'value' : (789,1004,846,1032)
    },
    'AEML GEN.' : {
            'label' : (922,687,1041,716),
            'value' : (1081,692,1175,717)
    },
    'CS GEN. TTL.' : {
            'label' : (1341,998,1492,1029),
            'value' : (1549,1001,1616,1023)
    },
    'KK’ PARA' : {
            'label' : (1346,708,1457,730),
            'value' : (1560,711,1626,732)
    },
    'TARPR PH-I' : {
            'label' : (1341,730,1484,757),
            'value' : (1556,733,1626,755)
    },
    'TARPR PH-II' : {
            'label' : (1341,750,1490,782),
            'value' : (1556,757,1626,781)
    },
    'SSP' : {
            'label' : (1341,800,1401,823),
            'value' : (1557,802,1626,825)
    },
    'RGPPL' : {
            'label' : (1343,822,1421,849),
            'value' : (1560,820,1620,850)
    },
    'GANDHAR' : {
            'label' : (1341,660,1446,689),
            'value' : (1562,656,1623,685)
    },
    'CS EXCH' : {
            'label' : (920,303,1021,338),
            'value' : (1090,309,1172,334)
    },
    # STATE DEMAND (including Mumbai!)
    'DEMAND' : {
            'label' : (932,1003,1021,1030),
            'value' : (1080,996,1167,1018)
    },
    # RE TTL
    'TTL' : {
            'label' : (597,1035,663,1056),
            'value' : (783,1032,845,1056)
    },
    'TTL (IPP/CPP+RE)' : {
            'label' : (594,1072,765,1098),
            'value' : (786,1068,847,1093)
    },
    'SOLAR TTL' : {
            'label' : (592,577,715,605),
            'value' : (772,583,814,602)
    },
    'PIONEER' : {
            'label' : (592,910,694,929),
            'value' : (794,910,844,927)
    }
}

generation_map = {
    'biomass' : {
        'add': ['COGEN'],
        'subtract': []
    },
    'coal' : {
        'add': ['THERMAL',
                'TTL (IPP/CPP+RE)',
                'TPC THM.',
                'CS GEN. TTL.',
                'AEML GEN.',
                'SOLAR TTL'],
        'subtract': ['TTL',
                     'PIONEER',
                     'SSP',
                     'RGPPL',
                     'TARPR PH-I',
                     'TARPR PH-II',
                     'KK’ PARA',
                     'GANDHAR']
    },
    'gas': {
        'add': ['GAS',
                'PIONEER',
                'GANDHAR',
                'RGPPL'],
        'subtract': []
    },
    'hydro' : {
        'add': ['HYDRO',
                'TPC HYD.',
                'SSP'],
        'subtract': []
    },
    'nuclear' : {
        'add': ['TARPR PH-I',
                'TARPR PH-II',
                'KK’ PARA'],
        'subtract': []
    },
    'solar' : {
        'add': ['MS SOLAR'],
        'subtract': []
    },
    'wind' : {
        'add': ['MS WIND'],
        'subtract': []
    },
    'unknown' : {
        'add': ['OTHR+SMHYD'],
        'subtract': []
    }
}

# list of values that belong to Central State production
CS = ['SSP',
      'RGPPL',
      'TARPR PH-I',
      'TARPR PH-II',
      'KK’ PARA',
      'GANDHAR',
      'CS GEN. TTL.']

# converts image into a black and white
def RGBtoBW(pil_image):
    # pylint: disable=no-member
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    image = cv2.threshold(image, 0, 255,
                          cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return Image.fromarray(image)

# performs text recognition on given location and source image
def recognize(location, source, lang):
    img = source.crop(location)
    img = RGBtoBW(img)
    img = ImageOps.invert(img)
    text = pytesseract.image_to_string(img, lang=lang, config='--psm 7')

    return text, img

# ignores highly indistinguishable characters
def areEqual(str1,str2):
    chars = {
        '{':'(',
        '}': ')',
        'T': 'L',
        'I': 'L',
        'P': 'E',
        ' ': ''
    }
    for key, value in chars.items():
        str1 = str1.replace(key,value)
        str2 = str2.replace(key,value)
    return str1.lower() == str2.lower()


# TODO: this function actually fetches consumption data
def fetch_production(zone_key='IN-MH', session=None, target_datetime = None,
                     logger=logging.getLogger(__name__)):

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    dt = arrow.now('Asia/Kolkata').floor('minute').datetime

    data = {
        'zoneKey': 'IN-MH',
        'datetime': dt,
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'unknown': 0.0
        },
        'storage': {},
        'source': 'mahasldc.in',
    }

    image = imread(url)
    image = Image.fromarray(image)  # create PIL image

    labels = {}
    values = {}

    # read in label-value pairs from the image as specified in locations dict
    for type, locs in locations.items():
        label,_ = recognize(locs['label'], image, 'eng')
        value, _ = recognize(locs['value'], image, 'digits_comma')
        labels[type] = label
        values[type] = max( [float(value),0] )

        assert (areEqual(label,type)), \
            'Wrongly regognized label `{}` as `{}`'.format(type, label)

    # fraction of central state production that is exchanged with Maharashtra
    share = values['CS EXCH'] / values['CS GEN. TTL.']

    for type, plants in generation_map.items():
        for plant in plants['add']:
            fac = share if plant in CS else 1  # add only a fraction of central state plant consumption
            data['production'][type] += fac * values[plant]
        for plant in plants['subtract']:
            fac = share if plant in CS else 1
            data['production'][type] -= fac * values[plant]

    # Sum over all production types is expected to equal the total demand
    demand_diff = sum( data['production'].values() ) - values['DEMAND']
    assert (abs( demand_diff) < 30), \
        'Production types do not add up to total demand. Difference: {}'.format(demand_diff)

    return data


if __name__ == '__main__':

    print( fetch_production() )
    