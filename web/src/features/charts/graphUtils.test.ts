import { ZoneDetail } from 'types';
import { Mode } from 'utils/constants';

import {
  extractLinkFromSource,
  getElectricityProductionValue,
  getRatioPercent,
  getTotalElectricityAvailable,
  getTotalEmissionsAvailable,
} from './graphUtils';

describe('getRatioPercent', () => {
  it('handles 0 of 0', () => {
    const actual = getRatioPercent(0, 0);
    expect(actual).to.deep.eq(0);
  });
  it('handles 10 of 0', () => {
    const actual = getRatioPercent(10, 0);
    expect(actual).to.deep.eq('?');
  });
  it('handles 0 of 10', () => {
    const actual = getRatioPercent(0, 10);
    expect(actual).to.deep.eq(0);
  });
  it('handles 5 of 5', () => {
    const actual = getRatioPercent(5, 5);
    expect(actual).to.deep.eq(100);
  });
  it('handles 1 of 5', () => {
    const actual = getRatioPercent(1, 5);
    expect(actual).to.deep.eq(20);
  });
});

describe('getElectricityProductionValue', () => {
  it('handles production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 61_370,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: 41_161,
    });
    expect(actual).to.deep.eq(41_161);
  });

  it('handles storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 20_222.25,
      isStorage: true,
      generationTypeStorage: -3738.75,
      generationTypeProduction: 11_930.25,
    });
    expect(actual).to.deep.eq(3738.75);
  });

  it('handles missing storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: true,
      generationTypeStorage: null,
      generationTypeProduction: 999,
    });
    expect(actual).to.deep.eq(null);
  });

  it('handles zero storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: true,
      generationTypeStorage: 0,
      generationTypeProduction: 999,
    });
    expect(actual).to.deep.eq(0);
  });

  it('handles zero production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: 0,
    });
    expect(actual).to.deep.eq(0);
  });

  it('handles null production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 16,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: null,
    });
    expect(actual).to.deep.eq(null);
  });
});

describe('getTotalEmissionsAvailableOrElectricityAvailable', () => {
  const zoneData = {
    totalCo2Production: 100,
    totalCo2Consumption: 5,
    totalConsumption: 50,
    totalCo2Discharge: 50,
    totalProduction: 200,
    totalDischarge: 50,
    totalImport: 100,
    totalCo2Import: 25,
  } as ZoneDetail;

  it('handles emissions for consumption', () => {
    const actual = getTotalEmissionsAvailable(zoneData, Mode.CONSUMPTION);
    expect(actual).to.deep.eq(175);
  });

  it('handles power for consumption', () => {
    const actual = getTotalElectricityAvailable(zoneData, Mode.CONSUMPTION);
    expect(actual).to.deep.eq(350);
  });

  it('handles emissions for production', () => {
    const actual = getTotalEmissionsAvailable(zoneData, Mode.PRODUCTION);
    expect(actual).to.deep.eq(150);
  });

  it('handles power for production', () => {
    const actual = getTotalElectricityAvailable(zoneData, Mode.PRODUCTION);
    expect(actual).to.deep.eq(250);
  });

  it('returns 0 when productionValue is 0', () => {
    const actual = getTotalElectricityAvailable(
      { ...zoneData, totalProduction: 0, totalDischarge: 0 },
      Mode.PRODUCTION
    );
    expect(actual).to.deep.eq(0);
  });
  it('returns NaN when missing productionValue', () => {
    const actual = getTotalElectricityAvailable(
      { ...zoneData, totalProduction: null },
      Mode.PRODUCTION
    );
    expect(actual).to.deep.eq(Number.NaN);
  });
});

describe('extractLinkFromSource', () => {
  const sourceLinkMapping = {
    source1: 'http://mappedlink1.com',
    source2: 'http://mappedlink2.com',
    Climatescope: 'https://www.global-climatescope.org/',
  };

  it('should return mapped link if source is in sourceLinkMapping', () => {
    expect(extractLinkFromSource('source1', sourceLinkMapping)).to.equal(
      'http://mappedlink1.com'
    );
    expect(extractLinkFromSource('source2', sourceLinkMapping)).to.equal(
      'http://mappedlink2.com'
    );
  });

  it('should work with a real link', () => {
    expect(extractLinkFromSource('Climatescope', sourceLinkMapping)).to.equal(
      'https://www.global-climatescope.org/'
    );
  });

  it('should return null if source does not include a dot', () => {
    expect(extractLinkFromSource('sourceWithoutDot', sourceLinkMapping)).to.be.null;
  });

  it('should return source if source includes http', () => {
    expect(
      extractLinkFromSource('http://sourceWithHttp.com', sourceLinkMapping)
    ).to.equal('http://sourceWithHttp.com');
  });

  it('should return source with http prefix if source includes a dot but not http', () => {
    expect(extractLinkFromSource('sourceWithDot.com', sourceLinkMapping)).to.equal(
      'http://sourceWithDot.com'
    );
  });
});
