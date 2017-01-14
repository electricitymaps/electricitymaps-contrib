## Data Science

The Electricity Map collects a unique dataset on the state of European Electricity Production. [Learn more on data sources per country here](https://github.com/corradio/electricitymap#data-sources).  

In this section we present a set of Python functions that let you pull this data locally and run your own analysis.

### Setup

If you use pip, you can install dependencies by running :

```
pip install -r requirements.txt
```

You can then import `utils` function in your python file :

```
from utils import *
```

### Documentation

#### get_production(countries, start_date, end_date, delta)

This function returns for each interval of `delta` minutes between `start_date` and `end_date`, the sources and amount of electricity produced for each country defined in `countries`.
Data are returned as a [pandas DataFrame](http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html).

Parameters :

- countries (*list*) - a list of country codes to pull.
- start_date (*string*) - start date. Date format is `YYYY-MM-DD`.
- end_date (*string*) - end date. Date format is `YYYY-MM-DD`.
- delta(*int*) - interval of timestamp between `start_date` and `end_date`. In minutes.

Example :

```python
from utils import get_production

df_production = get_production(['DE','FR'], '2016-12-23', '2016-12-24', 1440)

df_production.head()
```

Returns :

```
  country  production  sources                  timestamp
0      DE         NaN      oil  2016-12-23T00:00:00+00:00
1      DE      7562.0  nuclear  2016-12-23T00:00:00+00:00
2      DE      2828.0      gas  2016-12-23T00:00:00+00:00
3      DE      4229.0  biomass  2016-12-23T00:00:00+00:00
4      DE     19919.0     coal  2016-12-23T00:00:00+00:00
```
