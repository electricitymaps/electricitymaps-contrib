#!/usr/bin/python

"""
Test datapoints for quality.py
Each one is designed to test some part of the validation functions.
"""

import datetime

dt = datetime.datetime.now()

prod = {
        'biomass': 15.0,
        'coal': 130.0,
        'gas': 890.0,
        'hydro': 500.0,
        'nuclear': 345.7,
        'oil': 0.0,
        'solar': 60.0,
        'wind': 75.0,
        'geothermal': None,
        'unknown': 3.0
       }

c1 = {
      'consumption': 1374.0,
      'countryCode': 'FR',
      'datetime': dt,
      'production': prod,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

c2 = {
      'consumption': -1081.0,
      'countryCode': 'FR',
      'datetime': dt,
      'production': prod,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

c3 = {
      'consumption': None,
      'countryCode': 'FR',
      'datetime': dt,
      'production': prod,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

e1 = {
      'sortedCountryCodes': 'DK->NO',
      'datetime': dt,
      'netFlow': 73.0,
      'source': 'mysource.com'
      }

e2 = {
      'sortedCountryCodes': 'DK->NO',
      'netFlow': 73.0,
      'source': 'mysource.com'
      }

e3 = {
      'sortedCountryCodes': 'DK->NO',
      'datetime': 'At the 3rd beep the time will be......',
      'netFlow': 73.0,
      'source': 'mysource.com'
      }

future = datetime.datetime.now() + datetime.timedelta(seconds=5*60)

e4 = {
      'sortedCountryCodes': 'DK->NO',
      'datetime': future,
      'netFlow': 73.0,
      'source': 'mysource.com'
      }

p1 = {
      'countryCode': 'FR',
      'production': prod,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p2 = {
      'production': prod,
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p3 = {
      'countryCode': 'FR',
      'production': prod,
      'datetime': '13th May 2017',
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p4 = {
      'countryCode': 'BR',
      'production': prod,
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p5 = {
      'countryCode': 'BR',
      'production': prod,
      'datetime': future,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p6 = {
      'countryCode': 'FR',
      'production': {
              'biomass': 10.0,
              'coal': None,
              'gas': 780.0,
              'hydro': 340.2,
              'nuclear': 2390.0,
              'oil': None,
              'solar': 49.0,
              'wind': 0.0,
              'geothermal': 453.8,
              'unknown': None
             },
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p7 = {
      'countryCode': 'CH',
      'production': {
              'biomass': 10.0,
              'coal': None,
              'gas': 780.0,
              'hydro': 340.2,
              'nuclear': 2390.0,
              'oil': None,
              'solar': 49.0,
              'wind': 0.0,
              'geothermal': 453.8,
              'unknown': None
             },
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p8 = {
      'countryCode': 'FR',
      'production': {
              'biomass': 10.0,
              'coal': 230.6,
              'gas': 780.0,
              'hydro': 340.2,
              'nuclear': 2390.0,
              'oil': 0.0,
              'solar': 49.0,
              'wind': 0.0,
              'geothermal': -453.8,
              'unknown': 0.0
             },
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }

p9 = {
      'countryCode': 'FR',
      'production': {
              'biomass': 10.0,
              'coal': 230.6,
              'gas': 780.0,
              'hydro': 340.2,
              'nuclear': 2390.0,
              'oil': 0.0,
              'solar': 49.0,
              'wind': 0.0,
              'geothermal': 453.8,
              'unknown': 10.0
             },
      'datetime': dt,
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
      }
