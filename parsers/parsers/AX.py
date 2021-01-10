#!/usr/bin/env python3
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# Numpy and PIL are used to process the image
import numpy as np
from PIL import Image


def _get_masks(session=None):
    Minus = np.array([[[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255], [255, 255, 255], [255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Minus = Image.fromarray(Minus)
    
    Dot = np.array([[[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255], [255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]]], dtype=np.uint8)
    Dot = Image.fromarray(Dot)

    Zero = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Zero = Image.fromarray(Zero)

    One = np.array([[[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    One = Image.fromarray(One)

    Two = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Two = Image.fromarray(Two)

    Three = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype =np.uint8)
    Three = Image.fromarray(Three)

    Four = np.array([[[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype=np.uint8)
    Four = Image.fromarray(Four)

    Five = np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Five = Image.fromarray(Five)

    Six = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0], [255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255], [255, 255, 255], [255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 255, 255]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0],[0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 255, 255]],
     [[255, 255, 255], [255, 255, 255], [255, 255, 255],[255, 255, 255], [255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Six = Image.fromarray(Six)

    Seven = np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Seven = Image.fromarray(Seven)

    Eight = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0], [255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0], [0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255], [0, 0, 0],[0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255],[255, 255, 255]]], dtype = np.uint8)
    Eight = Image.fromarray(Eight)

    Nine = np.array([[[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[0, 0, 0],[0, 0, 0],[255, 255, 255],[255, 255, 255],[0, 0, 0],[0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[0, 0, 0], [0, 0, 0], [255, 255, 255], [255, 255, 255], [0, 0, 0], [0, 0, 0]],
     [[255, 255, 255],[0, 0, 0],[0, 0, 0],[0, 0, 0],[0, 0, 0],[255, 255, 255]],
     [[255, 255, 255],[255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255]]], dtype=np.uint8)
    Nine = Image.fromarray(Nine)
    
    shorts = ['-','.','0','1','2','3','4','5','6','7','8','9']
    masks = [Minus, Dot, Zero, One, Two, Three, Four, Five, Six, Seven, Eight, Nine]
    
    return dict(zip(shorts,masks))
    

def _fetch_data(session=None):
    # Load masks for reading numbers from the image
    # Create a dictionary of symbols and their pixel masks
    mapping = _get_masks(session)

    # Download the updating image from Kraftnät Åland
    r = session or requests.session()
    
    url = 'http://194.110.178.135/grafik/stamnat.php'
    
    im = Image.open(r.get(url, stream=True).raw)
    # Get timestamp
    fetchtime = arrow.utcnow().floor('second').to('Europe/Mariehamn')
    
    # "data" is a height x width x 3 RGB numpy array
    data = np.array(im)   
    #red, green, blue, alpha = data.T # Temporarily unpack the bands for readability
    red, green, blue = data.T
    # Color non-blue areas in the image with white
    blue_areas = ((red == 0) & (green == 0) & (blue == 255))
    data[~blue_areas.T] = (255, 255, 255)
    # Color blue areas in the image with black
    data[blue_areas.T] = (0, 0, 0)
    
    # Transform the array back to image
    im = Image.fromarray(data)
    
    shorts = mapping.keys()

    # check import from Sweden
    SE3Flow = []
    for x in range(80, 130-6):
        for abr in shorts:
            im1 = im.crop((x, 443, x+6, 452))
            if im1 == mapping[abr]:
                SE3Flow.append(abr)
    SE3Flow = "".join(SE3Flow)
    SE3Flow = round(float(SE3Flow),1)

    # export Åland-Finland(Kustavi/Gustafs)
    
    GustafsFlow=[]
    for x in range(780, 825-6):
        for abr in shorts:
            im1 = im.crop((x, 43, x+6, 52))
            if im1 == mapping[abr]:
                GustafsFlow.append(abr)
    GustafsFlow = "".join(GustafsFlow)
    GustafsFlow = round(float(GustafsFlow),1)
    
    # Reserve cable import Naantali-Åland
    # Åland administration does not allow export
    # to Finland through this cable
    FIFlow = []
    for x in range(760, 815-6):
        for abr in shorts:
            im1 = im.crop((x, 328, x+6, 337))
            if im1 == mapping[abr]:
                FIFlow.append(abr)
    FIFlow = "".join(FIFlow)
    FIFlow = round(float(FIFlow),1)


    # The shown total consumption is not reliable according to the TSO
    # Consumption
    # Cons = []
    # for x in range(650, 700-6):
    #    for abr in shorts:
    #        im1 = im.crop((x, 564, x+6, 573))
    #        if im1 == mapping[abr]:
    #            Cons.append(abr)
    # Cons = "".join(Cons)
    # Cons = round(float(Cons),1)

    # Wind production
    WProd = []
    for x in range(650, 700-6):
        for abr in shorts:
            im1 = im.crop((x, 576, x+6, 585))
            if im1 == mapping[abr]:
                WProd.append(abr)
    WProd = "".join(WProd)
    WProd = round(float(WProd),1)

    # Fossil fuel production
    FProd = []
    for x in range(650, 700-6):
        for abr in shorts:
            im1 = im.crop((x, 588, x+6, 597))
            if im1 == mapping[abr]:
                FProd.append(abr)
    FProd = "".join(FProd)
    FProd = round(float(FProd),1)
    
    # Both are confirmed to be import from Finland by the TSO
    FIFlow = FIFlow+GustafsFlow
    
    # Calculate sum of exchanges
    SumExchanges = SE3Flow+FIFlow
    
    # Calculate total production
    TotProd = FProd+WProd
    
    # Calculate total consumption
    Cons = round(TotProd + SumExchanges,1)
    
    # The production that is not fossil fuel or wind based is unknown
    # Impossible to estimate with current data
    # UProd = TotProd - WProd - FProd
    
    obj = dict({'production':TotProd,'consumption':Cons,'wind':WProd,
               'fossil':FProd,'SE3->AX':SE3Flow,
               'FI->AX':FIFlow,'fetchtime':fetchtime})
    
    return obj


def fetch_production(zone_key='AX', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    obj = _fetch_data(session)

    data = {
        'zoneKey': zone_key,
        'production': {},
        'storage': {},
        'source': 'kraftnat.aland.fi',
        'datetime': arrow.get(obj['fetchtime']).datetime
    }
    data['production']['biomass'] = None
    data['production']['coal'] = 0
    data['production']['gas'] = 0
    data['production']['hydro'] = None
    data['production']['nuclear'] = 0
    data['production']['oil'] = obj['fossil']
    data['production']['solar'] = None
    data['production']['wind'] = obj['wind']
    data['production']['geothermal'] = None
    data['production']['unknown'] = None
    
    return data


def fetch_consumption(zone_key='AX', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    obj = _fetch_data(session)
    
    data = {
        'zoneKey': zone_key,
        'datetime': arrow.get(obj['fetchtime']).datetime,
        'consumption': obj['consumption'],
        'source': 'kraftnat.aland.fi'
    }
    
    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    obj = _fetch_data(session)

    data = {
        'sortedZoneKeys': '->'.join(sorted([zone_key1, zone_key2])),
        'source': 'kraftnat.aland.fi',
        'datetime': arrow.get(obj['fetchtime']).datetime
    }

    # Country codes are sorted in order to enable easier indexing in the database
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    # Here we assume that the net flow returned by the api is the flow from
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    
    if '->'.join(sorted([zone_key1, zone_key2])) in ['AX->SE', 'AX->SE-SE3']:
        netFlow = obj['SE3->AX']
         
    elif '->'.join(sorted([zone_key1, zone_key2]))== 'AX->FI':
        netFlow = obj['FI->AX'] # Import is positive
    
    # The net flow to be reported should be from the first country to the second
    # (sorted alphabetically). This is NOT necessarily the same direction as the flow
    # from country1 to country2
    
    #  AX is before both FI and SE
    data['netFlow'] =  round(-1*netFlow,1)

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_consumption() ->')
    print(fetch_consumption())
    print('fetch_exchange(AX, FI) ->')
    print(fetch_exchange('FI', 'AX'))
    print('fetch_exchange(AX, SE) ->')
    print(fetch_exchange('SE', 'AX'))
