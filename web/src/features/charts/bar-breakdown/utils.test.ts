import {
  convertPrice,
  ExchangeDataType,
  getDataBlockPositions,
  getElectricityProductionValue,
  getExchangeCo2Intensity,
  getExchangeData,
  getExchangesToDisplay,
  getProductionData,
} from './utils';

const zoneDetailsData = {
  co2intensity: 187.32,
  co2intensityProduction: 190.6,
  zoneKey: 'PT',
  fossilFuelRatio: 0.3,
  fossilFuelRatioProduction: 0.3,
  renewableRatio: 0.7,
  renewableRatioProduction: 0.7,
  stateDatetime: '2022-11-28T07:00:00.000Z',
  _isFinestGranularity: true,
  capacity: {
    'battery storage': null,
    biomass: 700,
    coal: 0,
    gas: 4520,
    geothermal: 0,
    hydro: 4578,
    'hydro storage': 3585,
    nuclear: 0,
    oil: 0,
    solar: 1616,
    unknown: null,
    wind: 5389,
  },
  dischargeCo2Intensities: {
    battery: 136.442_667_362_438_53,
    hydro: 136.442_667_362_438_53,
  },
  dischargeCo2IntensitySources: {
    battery: 'electricityMap, 2021 average',
    hydro: 'electricityMap, 2021 average',
  },
  estimationMethod: undefined,
  exchange: { ES: -934 },
  exchangeCapacities: {},
  exchangeCo2Intensities: { ES: 187.32 },
  isValid: true,
  maxCapacity: 5389,
  maxDischarge: 395,
  maxExport: 934,
  maxExportCapacity: 3000,
  maxImport: 0,
  maxImportCapacity: 500,
  maxProduction: 2365,
  maxStorage: 0,
  maxStorageCapacity: 3585,
  price: { currency: 'EUR', value: 120 },
  production: {
    biomass: 350,
    coal: 0,
    gas: 1930,
    geothermal: null,
    hydro: 1445,
    nuclear: null,
    oil: null,
    solar: 17,
    unknown: 29,
    wind: 2365,
  },
  productionCo2Intensities: {
    biomass: 439.145_806,
    coal: 1099.976_527,
    gas: 492.109_361,
    geothermal: 38,
    hydro: 10.7,
    nuclear: 5.13,
    oil: 1124.903_938,
    solar: 25.6,
    unknown: 700,
    wind: 12.62,
  },
  productionCo2IntensitySources: {
    biomass: 'EU-ETS, ENTSO-E 2021',
    coal: 'eGrid 2020; Oberschelp, Christopher, et al. "Global emission hotspots of coal power generation."',
    gas: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    geothermal: 'IPCC 2014',
    hydro: 'UNECE 2022',
    nuclear: 'UNECE 2022',
    oil: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    solar: 'INCER ACV',
    unknown: 'assumes thermal (coal, gas, oil or biomass)',
    wind: 'UNECE 2022, WindEurope "Wind energy in Europe, 2021 Statistics and the outlook for 2022-2026" Wind Europe Proceedings (2021)',
  },
  source: ['entsoe.eu'],
  storage: { battery: null, hydro: -395 },
  totalCo2Discharge: 53_894_853.608_163_215,
  totalCo2Export: 174_956_880,
  totalCo2Import: 0,
  totalCo2NetExchange: -174_956_880,
  totalCo2Production: 1_169_515_098.83,
  totalCo2Consumption: 1_232_232_232,
  totalCo2Storage: 0,
  totalConsumption: 5597,
  totalDischarge: 395,
  totalExport: 934,
  totalImport: 0,
  totalProduction: 6136,
  totalStorage: 0,
};

const productionData = [
  {
    isStorage: false,
    production: 350,
    storage: undefined,
    capacity: 700,
    mode: 'biomass',
    gCo2eq: 153_701_032.1,
  },
  {
    isStorage: false,
    production: null,
    storage: undefined,
    capacity: 0,
    mode: 'geothermal',
    gCo2eq: 0,
  },
  {
    isStorage: false,
    storage: -395,
    production: 1445,
    capacity: 4578,
    mode: 'hydro',
    gCo2eq: 15_461_500,
  },
  {
    isStorage: false,
    production: 17,
    storage: undefined,
    capacity: 1616,
    mode: 'solar',
    gCo2eq: 435_200,
  },
  {
    isStorage: false,
    production: 2365,
    storage: undefined,
    capacity: 5389,
    mode: 'wind',
    gCo2eq: 29_846_300,
  },
  {
    isStorage: false,
    production: null,
    storage: undefined,
    capacity: 0,
    mode: 'nuclear',
    gCo2eq: 0,
  },
  {
    isStorage: true,
    storage: null,
    capacity: null,
    mode: 'battery storage',
    production: undefined,
    gCo2eq: 0,
  },
  {
    isStorage: true,
    storage: -395,
    production: 1445,
    capacity: 3585,
    mode: 'hydro storage',
    gCo2eq: -53_894_853.608_163_215,
  },
  {
    isStorage: false,
    production: 0,
    storage: undefined,
    capacity: 0,
    mode: 'coal',
    gCo2eq: 0,
  },
  {
    isStorage: false,
    production: 1930,
    storage: undefined,
    capacity: 4520,
    mode: 'gas',
    gCo2eq: 949_771_066.729_999_9,
  },
  {
    isStorage: false,
    production: null,
    storage: undefined,
    capacity: 0,
    mode: 'oil',
    gCo2eq: 0,
  },
  {
    isStorage: false,
    production: 29,
    storage: undefined,
    capacity: null,
    mode: 'unknown',
    gCo2eq: 20_300_000,
  },
];

const exchangeData: ExchangeDataType[] = [
  {
    exchange: -934,
    zoneKey: 'ES',
    gCo2eqPerkWh: 187.32,
    gCo2eq: -2.915_948,
    exchangeCapacityRange: [-1000, 1000],
  },
  {
    exchange: 200,
    zoneKey: 'FR',
    gCo2eqPerkWh: 999.32,
    gCo2eq: 45.915_948,
    exchangeCapacityRange: [0, 1000],
  },
];

describe('getProductionData', () => {
  it('returns correct data', () => {
    const result = getProductionData(zoneDetailsData);
    // TODO: Match snapshot
    expect(result).to.deep.eq(productionData);
  });
});

describe('getElectricityProductionValue', () => {
  it('handles production value', () => {
    const result = getElectricityProductionValue({
      capacity: 1000,
      isStorage: false,
      production: 500,
      storage: 0,
    });
    expect(result).to.eq(500);
  });
  it('handles missing production value with zero capacity', () => {
    const result = getElectricityProductionValue({
      capacity: 0,
      isStorage: false,
      production: null,
      storage: 0,
    });
    expect(result).to.eq(0);
  });

  it('handles missing production value', () => {
    const result = getElectricityProductionValue({
      capacity: 100,
      isStorage: false,
      production: null,
      storage: 0,
    });

    expect(result).to.eq(null);
  });
  it('handles storage', () => {
    const result = getElectricityProductionValue({
      capacity: 100,
      isStorage: true,
      production: null,
      storage: 300,
    });
    expect(result).to.eq(-300);
  });
  it('handles zero storage', () => {
    const result = getElectricityProductionValue({
      capacity: 100,
      isStorage: true,
      production: null,
      storage: 0,
    });
    expect(result).to.eq(0);
  });
  it('handles missing storage', () => {
    const result = getElectricityProductionValue({
      capacity: 100,
      isStorage: true,
      production: null,
      storage: null,
    });
    expect(result).to.eq(null);
  });
});

describe('getDataBlockPositions', () => {
  it('returns correct data', () => {
    const result = getDataBlockPositions(productionData.length, exchangeData);
    expect(result).to.deep.eq({
      exchangeFlagX: 50,
      exchangeHeight: 40,
      exchangeY: 262,
      productionY: 22,
      productionHeight: 240,
    });
  });
});

describe('getExchangesToDisplay', () => {
  it('shows aggregated exchanges only when required', () => {
    const ZoneStates = {
      date1: {
        ...zoneDetailsData,
        exchange: { AT: -934, BE: 934, NO: -934, 'NO-NO2': -500 },
      },
    };
    const result = getExchangesToDisplay(true, 'DE', ZoneStates);
    expect(result).to.deep.eq(['AT', 'BE', 'NO']);
  });
  it('shows non-aggregated exchanges only when required', () => {
    const ZoneStates = {
      date1: {
        ...zoneDetailsData,
        exchange: { AT: -934, BE: 934, NO: -934, 'NO-NO2': -500 },
      },
    };
    const result = getExchangesToDisplay(false, 'DE', ZoneStates);
    expect(result).to.deep.eq(['AT', 'BE', 'NO-NO2']);
  });
  it('handles empty exchange', () => {
    const ZoneStates = {
      date1: {
        ...zoneDetailsData,
        exchange: {},
      },
    };
    const result = getExchangesToDisplay(false, 'DE', ZoneStates);
    expect(result).to.deep.eq([]);
  });
});

describe('getExchangeData', () => {
  it('returns array of exchange data', () => {
    const exchangeCapacity: [number, number] = [-1000, 1000];
    const exchangeCapacitiesZoneDetailsData = {
      ...zoneDetailsData,
      exchange: { AT: -934, ES: 934 },
      exchangeCapacities: { ES: exchangeCapacity, AT: exchangeCapacity },
    };
    const result = getExchangeData(['ES', 'AT'], true, exchangeCapacitiesZoneDetailsData);

    expect(result).to.deep.eq([
      {
        exchange: 934,
        exchangeCapacityRange: [-1000, 1000],
        zoneKey: 'ES',
        gCo2eqPerkWh: 187.32,
        gCo2eq: 174_956_880,
      },
      {
        exchange: -934,
        exchangeCapacityRange: [-1000, 1000],
        zoneKey: 'AT',
        gCo2eqPerkWh: 187.32,
        gCo2eq: -174_956_880,
      },
    ]);
  });
  it('handles missing exchange capacity', () => {
    const exchangeCapacitiesZoneDetailsData = {
      ...zoneDetailsData,
    };
    const result = getExchangeData(['ES'], true, exchangeCapacitiesZoneDetailsData);

    expect(result).to.deep.eq([
      {
        exchange: -934,
        exchangeCapacityRange: [0, 0],
        zoneKey: 'ES',
        gCo2eqPerkWh: 187.32,
        gCo2eq: -174_956_880,
      },
    ]);
  });
  it('handles missing exchange data', () => {
    const exchangeCapacity: [number, number] = [-1000, 1000];
    const exchangeCapacitiesZoneDetailsData = {
      ...zoneDetailsData,
      exchange: {},
      exchangeCapacity: { ES: exchangeCapacity },
    };
    const result = getExchangeData(['ES'], true, exchangeCapacitiesZoneDetailsData);

    expect(result).to.deep.equal([
      {
        exchange: undefined,
        exchangeCapacityRange: [0, 0],
        zoneKey: 'ES',
        gCo2eqPerkWh: 187.32,
        gCo2eq: Number.NaN,
      },
    ]);
  });
});

describe('getExchangeCo2Intensity', () => {
  it('returns exchange Co2 intensity if exhange value is greater than or equal to 0', () => {
    const exchangeCapacitiesZoneDetailsData = {
      ...zoneDetailsData,
      exchange: { ES: 1000 },
      exchangeCo2Intensities: { ES: 999 },
    };

    const result = getExchangeCo2Intensity('ES', exchangeCapacitiesZoneDetailsData, true);
    expect(result).to.eq(999);
  });
  describe('when exchange value is less than 0', () => {
    it('returns Co2 insensity when in Consumption mode', () => {
      const exchangeCapacitiesZoneDetailsData = {
        ...zoneDetailsData,
        exchange: { ES: -1000 },
        exchangeCo2Intensities: { ES: 999 },
      };

      const result = getExchangeCo2Intensity(
        'ES',
        exchangeCapacitiesZoneDetailsData,
        true
      );
      expect(result).to.eq(187.32);
    });
    it('returns Co2 insensity production when in Production mode', () => {
      const exchangeCapacitiesZoneDetailsData = {
        ...zoneDetailsData,
        exchange: { ES: -1000 },
        exchangeCo2Intensities: { ES: 999 },
      };

      const result = getExchangeCo2Intensity(
        'ES',
        exchangeCapacitiesZoneDetailsData,
        false
      );
      expect(result).to.eq(190.6);
    });
  });
});

describe('convertPrice', () => {
  it('dont convert USD to price/KWh', () => {
    const result = convertPrice(120, 'USD');
    expect(result).to.deep.eq({ value: 120, currency: 'USD', unit: 'MWh' });
  });

  it('handles missing currency', () => {
    const result = convertPrice(120, undefined);
    expect(result).to.deep.eq({ value: 120, currency: undefined, unit: 'MWh' });
  });

  it('handles missing price with EUR', () => {
    const result = convertPrice(undefined, 'EUR');
    expect(result).to.deep.eq({ value: undefined, currency: 'EUR', unit: 'MWh' });
  });

  it('handles missing price without EUR', () => {
    const result = convertPrice(undefined, 'USD');
    expect(result).to.deep.eq({ value: undefined, currency: 'USD', unit: 'MWh' });
  });

  it('handles missing price and currency', () => {
    const result = convertPrice(undefined, undefined);
    expect(result).to.deep.eq({ value: undefined, currency: undefined, unit: 'MWh' });
  });
});
