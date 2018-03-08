#!/usr/bin/env python3

# This parser gets all real time interconnection flows from the
# Central American Electrical Interconnection System (SIEPAC).

import arrow
import pandas as pd

url = 'http://www.enteoperador.org/newsite/flash/data.csv'


def read_data():
    """
    Reads csv data from the url.
    Returns a pandas dataframe.
    """

    df = pd.read_csv(url, index_col=False)

    return df


def connections(df):
    """
    Gets values for each interconnection.
    Returns a dictionary.
    """

    interconnections = {'GT->MX': df.iloc[0]['MXGU'],
                        'GT->SV': df.iloc[0]['GUES'],
                        'GT->HN': df.iloc[0]['GUHO'],
                        'HN->SV': df.iloc[0]['ESHO'],
                        'HN->NI': df.iloc[0]['HONI'],
                        'CR->NI': df.iloc[0]['NICR'],
                        'CR->PA': df.iloc[0]['CRPA']}

    return interconnections


def net(df):
    """
    Gets net production values for each country.  Uses system totals for Mexico.
    Returns a dictionary.
    """

    net_production = {}
    net_production['GT'] = df.iloc[0]['GENGUA'] - df.iloc[0]['DEMGUA']
    net_production['SV'] = df.iloc[0]['GENSAL'] - df.iloc[0]['DEMSAL']
    net_production['HN'] = df.iloc[0]['GENHON'] - df.iloc[0]['DEMHON']
    net_production['NI'] = df.iloc[0]['GENNIC'] - df.iloc[0]['DEMNIC']
    net_production['CR'] = df.iloc[0]['GENCRI'] - df.iloc[0]['DEMCRI']
    net_production['PA'] = df.iloc[0]['GENPAN'] - df.iloc[0]['DEMPAN']
    net_production['MX'] = df.iloc[0]['TOTALGEN'] - df.iloc[0]['TOTALDEM']

    return net_production


def flow_logic(net_production, interconnections):
    """
    Calculates flow direction for each interconnection using network flow and
    simultaneous equations.
    Returns a dictionary.
    """

    # Each country is modeled as a node with flows going either in or out of it.
    # Importing is given a negative flow while exporting is positive.

    PA = {'CR': 0}
    CR = {'PA': 0, 'NI': 0}
    NI = {'CR': 0, 'HN': 0}
    HN = {'GT': 0, 'SV': 0, 'NI': 0}
    SV = {'GT': 0, 'HN': 0}  # TODO: SV is assigned to but never used
    GT = {'MX': 0, 'HN': 0, 'SV': 0}

    def plusminus(value):
        """
        Takes a number and check its sign.
        Returns 1 if positive, -1 if negative and zero if zero.
        """

        if value > 0:
            newvalue = 1
        elif value < 0:
            newvalue = -1
        else:
            newvalue = 0

        return newvalue

    def flipsign(value):
        """
        Changes the sign of any number given apart from zero.
        1 -> -1
        -1 -> 1
        """

        newvalue = (-1) * value

        return newvalue

    flows = {'HN->NI': 0.0,
             'CR->NI': 0.0,
             'CR->PA': 0.0,
             'GT->HN': 0.0,
             'GT->MX': 0.0,
             'GT->SV': 0.0,
             'HN->SV': 0.0}

    # First we determine whether Mexico is importing or exporting using totals for the SIEPAC system.

    if net_production['MX'] < 0:
        # exporting
        GT['MX'] = -1
    else:
        GT['MX'] = 1

    # We then find the direction of the PA by exploiting the fact that it only has one interconnection.

    if net_production['PA'] > 0:
        # PA can only export to CR
        PA['CR'] = 1
        CR['PA'] = -1
    else:
        # PA importing from CR
        PA['CR'] = -1
        CR['PA'] = 1

    # Next we can find CR and NI flows using their net productions and process of elimination.

    PAN = interconnections['CR->PA'] * CR['PA']

    CR['NI'] = plusminus((net_production['CR'] - PAN) / interconnections['CR->NI'])
    NI['CR'] = flipsign(CR['NI'])
    NIC = interconnections['CR->NI'] * NI['CR']

    NI['HN'] = plusminus((net_production['NI'] - NIC) / interconnections['HN->NI'])
    HN['NI'] = flipsign(NI['HN'])

    # Now we use 3 simultaneous equations to find the remaining flows.  We can use the fact that
    # several flows are already known to our advantage.

    # a = interconnections['GT->SV']
    # b = interconnections['HN->SV']
    # c = interconnections['GT->HN']
    # MX = interconnections['GT->MX']*GT['MX']
    # HON = interconnections['HN->NI']*HN['NI']
    #
    # eqs = np.array([[a, b, 0], [a, 0, c], [0, b, c]])
    # res = np.array([net_production['SV'], net_production['GT']-MX, net_production['HN']-HON])
    #
    # solution = np.linalg.solve(eqs, res)
    #
    # #Factor to account for transmission losses.
    # GT['SV'] = plusminus(solution[0]+0.5)
    #
    # SV['GT'] = flipsign(GT['SV'])
    # SV['HN'] = plusminus(solution[1])
    # HN['SV'] = flipsign(SV['HN'])
    # GT['HN'] = plusminus(solution[2])
    # HN['GT'] = flipsign(GT['HN'])

    # Flows commented out are disabled until the maths behind determining their direction can be proved satisfactorily.
    flows['HN->NI'] = HN['NI']
    flows['CR->NI'] = CR['NI']
    flows['CR->PA'] = CR['PA']
    # flows['GT->HN'] = GT['HN']
    flows['GT->MX'] = GT['MX']
    # flows['GT->SV'] = GT['SV']
    # flows['HN->SV'] = SV['HN']

    return flows


def net_flow(interconnections, flows):
    """
    Combines interconnection values with flow directions.
    Returns a dictionary.
    """

    netflow = {k: interconnections[k] * flows[k] for k in interconnections}

    return netflow


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """
    Gets an exchange pair from the SIEPAC system.
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'CR->PA',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    getdata = read_data()
    connect = connections(getdata)
    nt = net(getdata)
    fl = flow_logic(nt, connect)
    netflow = net_flow(connect, fl)

    exchange = {}
    dt = arrow.now('UTC-6').floor('minute')
    zones = '->'.join(sorted([zone_key1, zone_key2]))

    if zones in netflow:
        exchange['netFlow'] = netflow[zones]
    else:
        raise NotImplementedError('This exchange is not implemented.')

    exchange.update(sortedZoneKeys=zones,
                    datetime=dt.datetime,
                    source='enteoperador.org')

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_exchange(CR, PA) ->')
    print(fetch_exchange('CR', 'PA'))
    print('fetch_exchange(CR, NI) ->')
    print(fetch_exchange('CR', 'NI'))
    print('fetch_exchange(HN, NI) ->')
    print(fetch_exchange('HN', 'NI'))
    print('fetch_exchange(GT, MX) ->')
    print(fetch_exchange('GT', 'MX'))
