# Adding a new country
It is very simple to add a new country. The Electricity Map backend runs a list of so-called *parsers* every 5min. Those parsers are responsible to fetch the generation mix for a given country (check out the existing list in the [parsers](https://github.com/corradio/electricitymap/tree/master/parsers) directory, or look at the [work in progress](https://github.com/tmrowco/electricitymap/issues?q=is%3Aissue+is%3Aopen+label%3Aparser)).

A parser is a python script that is expected to define the method `fetch_production` which returns the production mix at current time, in the format:

```python
def fetch_production(country_code='FR', session=None):
    return {
      'countryCode': 'FR',
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
```

The `session` object is a python request session that you can re-use to make HTTP requests.

The production values should never be negative. Use `null`, or ommit the key, if a specific production mode is not known.
Storage values can be both positive (when storing energy) or negative (when the storage is emptied).

The parser can also return an array of objects if multiple time values can be fetched. The backend will automatically update past values properly.
