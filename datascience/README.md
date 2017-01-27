## Data Science

The Electricity Map collects a unique dataset on the state of European Electricity Production. [Learn more on data sources per country here](https://github.com/corradio/electricitymap#data-sources).  

In this section we present a set of Python functions that let you pull this data locally and run your own analysis.

### Setup

If you use pip, you can install dependencies by running:

```
pip install -r requirements.txt
```

You can then import `utils` function in your python file:

```
from utils import *
```

### Examples
We recommend you to use [Jupyter Notebooks](http://jupyter.org/) to explore the datasets.
It can be installed by running:

```
pip install jupyter
```

You can then run the notebook server by running this command from the datascience folder:

```
jupyter notebook
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

Data returned :

- country - country that was passed in the `countries` parameter list.
- production - power produced (in MW).
- mode - production mode of electricity (oil,nuclear,gas,biomass,coal,solar,wind,hydro).
- timestamp - timestamp at which the fetch was performed.

Example :

```python
from utils import get_production

df_production = get_production(['DE','FR'], '2016-12-23', '2016-12-24', 1440)

df_production.head()
```

Returns :

```
  country  production     mode                  timestamp
0      DE         NaN      oil  2016-12-23T00:00:00+00:00
1      DE      7562.0  nuclear  2016-12-23T00:00:00+00:00
2      DE      2828.0      gas  2016-12-23T00:00:00+00:00
3      DE      4229.0  biomass  2016-12-23T00:00:00+00:00
4      DE     19919.0     coal  2016-12-23T00:00:00+00:00
```

#### get_exchange(countries, start_date, end_date, delta)

This function returns for each day between `start_date` and `end_date`, the electricity production exchanges for each country defined in `countries`. Data are returned as a [pandas DataFrame](http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html).

Parameters :

- countries (*list*) - a list of country codes to pull.
- start_date (*string*) - start date. Date format is `YYYY-MM-DD`.
- end_date (*string*) - end date. Date format is `YYYY-MM-DD`.
- delta(*int*) - interval of timestamp between `start_date` and `end_date`. In minutes.

Data returned :

- country_from - country that was passed in the `countries` parameter list.
- country_to - country with which the electricity was exchanged.
- timestamp - date for which the electricity exchange was computed.
- net_flow - power exchanged (in MW). Negative value are export of `country_from` to `country_to`. Positive value are import of `country_from` from `country_to`.

Example :

```python
from utils import get_exchange

df_exchange = get_exchange(['DE','FR'], '2016-12-23', '2016-12-24', 1440)

df_exchange.head()
```

Returns :

```
  country_from country_to                  timestamp net_flow
0           DE         FR  2016-12-23T00:00:00+00:00    176.0
1           DE         CH  2016-12-23T00:00:00+00:00  -2320.0
2           DE         NL  2016-12-23T00:00:00+00:00  -1840.0
3           DE         DK  2016-12-23T00:00:00+00:00    -79.0
4           DE         CZ  2016-12-23T00:00:00+00:00   -476.0
```

### Tips
#### Export as CSV to use in Excel
Use the `.to_csv()` method on a dataframe to export it to csv format on your computer. For instance:
```python
from utils import get_exchange
get_exchange(['DE','FR'], '2016-12-23', '2016-12-24', 1440).to_csv('myfilename.csv')
```

You can also run the command in one line from your shell:
```bash
python -c "from utils import get_exchange; get_exchange(['DE','FR'], '2016-12-23', '2016-12-24', 1440).to_csv('myfilename.csv')"
```
