# Production Parser

## Arguments

`zone_key`

> Type: `str` - Native Python string object. <br/>
> Description: <br/>
> Passed to the parser as a unique identifier for each zone.

---

`session`

> Type: `request.Session` - A Request Session object. <br/>
> Description: <br/>
> Passed to the parser in order to reuse an existing connection. Should default to `request.Session()`.

---

`target_datetime`

> Type: Datetime | None - Native python datetime or None. <br/>
> Description: <br/>
> Passed to the parser if the backend request to fetch data from a specific datetime. Should default to `None`.

---

`logger`

> Type: logging.Logger - Native python logging object. <br/>
> Description: <br/>
> Passed to the parser by the backend to enable public logging. Should default to `logging.getLogger(__name__)`.

## Return value signature

The parser should either return a dictionary or a list of dictionaries matching the following object:

```python
{
  'zoneKey': zone_key,
  # datetime is easiest passed as a datetime object parsed from the source.
  'datetime': datetime.datetime(2023, 2, 8, 17, 0, tzinfo=tzutc()),
  'production': {
      'biomass': 0.0,
      'coal': 0.0,
      'gas': 0.0,
      'hydro': 0.0,
      'nuclear': None, # Can also be omitted if it's not available.
      'oil': 0.0,
      'solar': 0.0,
      'wind': 0.0,
      'geothermal': 0.0,
      'unknown': 0.0
  },
  'capacity': {
      # If the same API provides capacities then you can return those as well, but you should not add additional API dependencies for it.
      'hydro': 0.0
  },
  'storage': {
      #NOTE: For storage negative values indicate discharge (production) and positive numbers charging (input).
      'hydro': 0.0,
  },
  'source': 'mysource.com'
}
```
