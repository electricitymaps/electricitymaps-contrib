# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_parser_outputs[DE] 1'] = {
    'datetime': GenericRepr('datetime.datetime(2021, 7, 22, 12, 0, tzinfo=tzutc())'),
    'production': {
        'biomass': 5078.0,
        'coal': 15006.0,
        'gas': 6682.0,
        'geothermal': 22.0,
        'hydro': 2202.0,
        'nuclear': 7885.0,
        'oil': 314.0,
        'solar': 26696.0,
        'unknown': 407.0,
        'wind': 2120.0
    },
    'source': 'entsoe.eu',
    'storage': {
        'hydro': 1604.0
    },
    'zoneKey': 'DE'
}

snapshots['test_parser_outputs[DK-DK1] 1'] = {
    'datetime': GenericRepr('datetime.datetime(2021, 7, 23, 4, 0, tzinfo=tzutc())'),
    'production': {
        'biomass': 122.0,
        'coal': 697.0,
        'gas': 86.0,
        'geothermal': None,
        'hydro': 1.0,
        'nuclear': None,
        'oil': 10.0,
        'solar': 24.0,
        'unknown': 2.0,
        'wind': 161.0
    },
    'source': 'entsoe.eu',
    'storage': {
        'hydro': None
    },
    'zoneKey': 'DK-DK1'
}

snapshots['test_parser_outputs[HR] 1'] = {
    'datetime': GenericRepr('datetime.datetime(2021, 7, 23, 6, 37, 5, tzinfo=tzutc())'),
    'production': {
        'solar': 9.919,
        'unknown': 1055.081,
        'wind': 104.0
    },
    'source': 'hops.hr',
    'zoneKey': 'HR'
}

snapshots['test_parser_outputs_exchange[BR-CS->BR-N] 1'] = {
    'datetime': GenericRepr('datetime.datetime(2021, 7, 23, 3, 37, tzinfo=tzoffset(None, -10800))'),
    'netFlow': -5129.374,
    'sortedZoneKeys': 'BR-CS->BR-N',
    'source': 'ons.org.br'
}

snapshots['test_parser_outputs_exchange[CA-MB->US-MIDW-MISO] 1'] = [
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 5, 0, tzinfo=tzutc())'),
        'netFlow': -388,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 4, 0, tzinfo=tzutc())'),
        'netFlow': 176,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 3, 0, tzinfo=tzutc())'),
        'netFlow': 893,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 2, 0, tzinfo=tzutc())'),
        'netFlow': 1154,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 1, 0, tzinfo=tzutc())'),
        'netFlow': 1097,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 21, 0, 0, tzinfo=tzutc())'),
        'netFlow': 1131,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 23, 0, tzinfo=tzutc())'),
        'netFlow': 1563,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 22, 0, tzinfo=tzutc())'),
        'netFlow': 1601,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 21, 0, tzinfo=tzutc())'),
        'netFlow': 1219,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 20, 0, tzinfo=tzutc())'),
        'netFlow': 1292,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 19, 0, tzinfo=tzutc())'),
        'netFlow': 1059,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 18, 0, tzinfo=tzutc())'),
        'netFlow': 1042,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 17, 0, tzinfo=tzutc())'),
        'netFlow': 1128,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 16, 0, tzinfo=tzutc())'),
        'netFlow': 965,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 15, 0, tzinfo=tzutc())'),
        'netFlow': 878,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 14, 0, tzinfo=tzutc())'),
        'netFlow': 739,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 13, 0, tzinfo=tzutc())'),
        'netFlow': 450,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 12, 0, tzinfo=tzutc())'),
        'netFlow': 135,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 11, 0, tzinfo=tzutc())'),
        'netFlow': -155,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 10, 0, tzinfo=tzutc())'),
        'netFlow': -114,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 9, 0, tzinfo=tzutc())'),
        'netFlow': -83,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 8, 0, tzinfo=tzutc())'),
        'netFlow': -144,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 7, 0, tzinfo=tzutc())'),
        'netFlow': -283,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 20, 6, 0, tzinfo=tzutc())'),
        'netFlow': -408,
        'sortedZoneKeys': 'CA-MB->US-MIDW-MISO',
        'source': 'eia.gov'
    }
]

snapshots['test_parser_outputs_exchange[RU-1->RU-2] 1'] = [
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 23, 6, 0, tzinfo=tzutc())'),
        'netFlow': 100.43110656738281,
        'sortedZoneKeys': 'RU-1->RU-2',
        'source': 'so-ups.ru'
    },
    {
        'datetime': GenericRepr('datetime.datetime(2021, 7, 23, 5, 0, tzinfo=tzutc())'),
        'netFlow': 136.66033935546875,
        'sortedZoneKeys': 'RU-1->RU-2',
        'source': 'so-ups.ru'
    }
]
