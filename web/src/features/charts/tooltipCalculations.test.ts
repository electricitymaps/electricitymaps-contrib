import { ZoneDetail } from 'types';
import { getExchangeTooltipData, getProductionTooltipData } from './tooltipCalculations';

const zoneDetailsData = {
  _isFinestGranularity: true,
  capacity: {
    'battery storage': 7,
    biomass: 2234,
    coal: 1818,
    gas: 12_752,
    geothermal: 16,
    hydro: 20_222.25,
    'hydro storage': 5053.47,
    nuclear: 61_370,
    oil: 2890,
    solar: 13_612,
    unknown: 1366,
    wind: 19_099,
  },
  co2intensity: 155.82,
  co2intensityProduction: 133.97,
  dischargeCo2Intensities: {
    battery: 54.190_888_929_032_22,
    hydro: 54.190_888_929_032_22,
  },
  dischargeCo2IntensitySources: {
    battery: 'Electricity Maps, 2021 average',
    hydro: 'Electricity Maps, 2021 average',
  },
  exchange: { BE: 1304, CH: 2602, DE: 3529, ES: 1745, GB: -2994, IT: 71, 'IT-NO': 71 },
  exchangeCapacities: { ES: [-2800, 2800], GB: [-3000, 3000] },
  exchangeCo2Intensities: {
    BE: 332.99,
    CH: 90.89,
    DE: 698.53,
    ES: 123.56,
    GB: 155.83,
    IT: 474.56,
    'IT-NO': 474.56,
  },
  fossilFuelRatio: 0.1928,
  fossilFuelRatioProduction: 0.1677,
  isValid: true,
  maxCapacity: 61_370,
  maxDischarge: 3738.75,
  maxExport: 2994,
  maxExportCapacity: 3000,
  maxImport: 3529,
  maxImportCapacity: 3000,
  maxProduction: 41_161,
  maxStorage: 0,
  maxStorageCapacity: 5053.47,
  price: { currency: 'EUR', value: 620.33 },
  production: {
    biomass: 653.25,
    coal: 1825.5,
    gas: 9403,
    geothermal: null,
    hydro: 11_930.25,
    nuclear: 41_161,
    oil: 1396.25,
    solar: 0,
    unknown: null,
    wind: 5186.75,
  },
  productionCo2Intensities: {
    biomass: 230,
    coal: 953.933_527_4,
    gas: 624.846_764,
    geothermal: 38,
    hydro: 10.7,
    nuclear: 5.13,
    oil: 1013.595_656_1,
    solar: 30.075,
    unknown: 700,
    wind: 12.62,
  },
  productionCo2IntensitySources: {
    biomass: 'BEIS 2021; IPCC 2014',
    coal: 'EU-ETS, ENTSO-E 2021; Oberschelp, Christopher, et al. "Global emission hotspots of coal power generation."',
    gas: 'EU-ETS, ENTSO-E 2021; IPCC 2014',
    geothermal: 'IPCC 2014',
    hydro: 'UNECE 2022',
    nuclear: 'UNECE 2022',
    oil: 'EU-ETS, ENTSO-E 2021; IPCC 2014',
    solar: 'INCER ACV',
    unknown: 'assumes thermal (coal, gas, oil or biomass)',
    wind: 'UNECE 2022, WindEurope "Wind energy in Europe, 2021 Statistics and the outlook for 2022-2026" Wind Europe Proceedings (2021)',
  },
  renewableRatio: 0.3009,
  renewableRatioProduction: 0.2857,
  source: 'opendata.reseaux-energies.fr',
  stateDatetime: '2022-12-12T17:00:00Z',
  storage: { battery: null, hydro: -3738.75 },
  totalCo2Discharge: 202_606_185.983_419_2,
  totalCo2Export: 466_555_020.000_000_06,
  totalCo2Import: 3_418_826_830,
  totalCo2NetExchange: 2_952_271_810,
  totalCo2Production: 9_586_586_600.990_326,
  totalCo2Storage: 0,
  totalConsumption: 81_551.75,
  totalDischarge: 3738.75,
  totalExport: 2994,
  totalImport: 9251,
  totalProduction: 71_556,
  totalStorage: 0,
  zoneKey: 'FR',
} as unknown as ZoneDetail;

describe('getProductionTooltipData', () => {
  it('returns correct data for nuclear', () => {
    const data = getProductionTooltipData('nuclear', zoneDetailsData, false);
    const expectedData = {
      capacity: 61_370,
      co2Intensity: 5.13,
      co2IntensitySource: 'UNECE 2022',
      displayByEmissions: false,
      totalElectricity: 84_545.75,
      totalEmissions: 13_208_019_616.973_745,
      production: 41_161,
      zoneKey: 'FR',
      storage: undefined,
      isExport: false,
      emissions: 211_155_930,
      usage: 41_161,
    };
    expect(data).toEqual(expectedData);
  });

  it('returns correct data for nuclear with displayEmissions', () => {
    const actual = getProductionTooltipData('nuclear', zoneDetailsData, true);
    const expected = {
      capacity: 61_370,
      co2Intensity: 5.13,
      co2IntensitySource: 'UNECE 2022',
      displayByEmissions: true,
      totalElectricity: 13_208_019_616.973_745,
      totalEmissions: 13_208_019_616.973_745,
      production: 41_161,
      zoneKey: 'FR',
      storage: undefined,
      isExport: false,
      emissions: 211_155_930,
      usage: 211_155_930,
    };
    expect(actual).toEqual(expected);
  });

  it('returns correct data for hydro storage', () => {
    const actual = getProductionTooltipData('hydro storage', zoneDetailsData, false);
    const expected = {
      capacity: 5053.47,
      co2Intensity: 54.190_888_929_032_22,
      co2IntensitySource: 'Electricity Maps, 2021 average',
      displayByEmissions: false,
      totalElectricity: 84_545.75,
      totalEmissions: 13_208_019_616.973_745,
      production: 11_930.25,
      zoneKey: 'FR',
      storage: -3738.75,
      isExport: false,
      emissions: 202_606_185.983_419_2,
      usage: 3738.75,
    };
    expect(actual).toEqual(expected);
  });

  it('returns 0 usage for zero production', () => {
    const actual = getProductionTooltipData('solar', zoneDetailsData, false);
    expect(actual.usage).toEqual(0);
    expect(actual.emissions).toEqual(0);
  });

  it('returns nan usage for null production', () => {
    const actual = getProductionTooltipData('geothermal', zoneDetailsData, false);
    expect(actual.usage).toEqual(Number.NaN);
  });

  it('handles data with all production modes missing', () => {
    const zoneDetailsDataWithMissingProductionModes = {
      ...zoneDetailsData,
      production: Object.fromEntries(
        Object.keys(zoneDetailsData.production).map((key) => [key, null])
      ),
    } as unknown as ZoneDetail;
    const data = getProductionTooltipData(
      'nuclear',
      zoneDetailsDataWithMissingProductionModes,
      false
    );
    const expectedData = {
      capacity: 61_370,
      co2Intensity: 5.13,
      co2IntensitySource: 'UNECE 2022',
      displayByEmissions: false,
      totalElectricity: 84_545.75,
      totalEmissions: 13_208_019_616.973_745,
      production: null,
      zoneKey: 'FR',
      storage: undefined,
      isExport: false,
      emissions: Number.NaN,
      usage: Number.NaN,
    };
    expect(data).toEqual(expectedData);
  });

  it('handles missing capacity', () => {
    const { capacity: _, ...zoneDetailsDataWithoutCapacity } = zoneDetailsData;
    const actual = getProductionTooltipData(
      'nuclear',
      zoneDetailsDataWithoutCapacity,
      false
    );

    expect(actual.usage).toEqual(41_161);
  });
});

describe('getExchangeTooltipData', () => {
  it('returns correct data for ES', () => {
    const actual = getExchangeTooltipData('ES', zoneDetailsData, false);
    const expected = {
      capacity: 2800,
      co2Intensity: 123.56,
      displayByEmissions: false,
      totalElectricity: 84_545.75,
      totalEmissions: 13_208_019_616.973_745,
      zoneKey: 'FR',
      isExport: false,
      emissions: 215_612_200,
      usage: 1745,
    };
    expect(actual).toEqual(expected);
  });

  it('returns correct data for non-existing exchange', () => {
    const actual = getExchangeTooltipData('XXX', zoneDetailsData, false);
    const expected = {
      capacity: undefined,
      co2Intensity: undefined,
      displayByEmissions: false,
      totalElectricity: 84_545.75,
      totalEmissions: 13_208_019_616.973_745,
      zoneKey: 'FR',
      isExport: false,
      emissions: Number.NaN,
      usage: Number.NaN,
    };
    expect(actual).toEqual(expected);
  });
});
