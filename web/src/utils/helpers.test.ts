import { renderHook } from '@testing-library/react';
import {
  useLocation,
  useMatch,
  useMatches,
  useNavigate,
  useParams,
} from 'react-router-dom';
import { zoneDetailMock } from 'stories/mockData';
import { ZoneDetail } from 'types';
import { describe, expect, it, vi } from 'vitest';

import {
  dateToDatetimeString,
  getCarbonIntensity,
  getDestinationPath,
  getFossilFuelRatio,
  getNetExchange,
  getProductionCo2Intensity,
  getRenewableRatio,
  useNavigateWithParameters,
} from './helpers';

describe('dateToDatetimeString', () => {
  it('returns the correct datetime string', () => {
    const actual = dateToDatetimeString(new Date('2023-01-01T12:00:00Z'));
    expect(actual).to.eq('2023-01-01T12:00:00Z');
  });
});

describe('getProductionCo2Intensity', () => {
  it('returns the correct value when the type is hydro', () => {
    const actual = getProductionCo2Intensity('hydro', zoneDetailMock);
    expect(actual).to.eq(10.7);
  });

  it('returns the correct value when the type is battery storage', () => {
    const actual = getProductionCo2Intensity('battery storage', zoneDetailMock);
    expect(actual).to.eq(0);
  });
});

describe('getFossilFuelRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0 }, p: { fr: 1 } }, true);
      expect(actual).to.eq(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 1 }, p: { fr: 0 } }, true);
      expect(actual).to.eq(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio({ c: { fr: null }, p: { fr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0.3 }, p: { fr: 0.7 } }, true);
      expect(actual).to.eq(0.7);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio({ c: { fr: 1 }, p: { fr: 0 } }, false);
      expect(actual).to.eq(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0 }, p: { fr: 1 } }, false);
      expect(actual).to.eq(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio({ c: { fr: null }, p: { fr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0.7 }, p: { fr: 0.3 } }, false);
      expect(actual).to.eq(0.7);
    });
  });
});

describe('getCarbonIntensity', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity({ c: { ci: 100 }, p: { ci: 200 } }, true);
      expect(actual).to.eq(100);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity({ c: { fr: null }, p: { fr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity({ c: { ci: 100 }, p: { ci: 200 } }, false);
      expect(actual).to.eq(200);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity({ c: { fr: null }, p: { fr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });
  });
});

describe('getRenewableRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio({ c: { rr: 0.5 }, p: { rr: 0.3 } }, true);
      expect(actual).to.eq(0.5);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio({ c: { rr: null }, p: { rr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio({ c: { rr: 0.5 }, p: { rr: 0.3 } }, false);
      expect(actual).to.eq(0.3);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio({ c: { rr: null }, p: { rr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });
  });
});

describe('getDestinationPath', () => {
  it('should return the correct URL when location.search and location.hash are empty', () => {
    const originalLocation = global.location;
    global.location = { ...global.location, search: '', hash: '' } as Location;

    const to = '/path';
    const result = getDestinationPath({ to });

    expect(result).toBe('/path');

    global.location = originalLocation; // Restore original location
  });

  it('should include zoneId when provided', () => {
    const result = getDestinationPath({ to: '/path', zoneId: 'FR' });
    expect(result).toBe('/path/FR');
  });

  it('should include timeRange when provided', () => {
    const result = getDestinationPath({ to: '/path', timeRange: 'hourly' });
    expect(result).toBe('/path/hourly');
  });

  it('should include datetime when provided', () => {
    const result = getDestinationPath({ to: '/path', datetime: '2024-03-20' });
    expect(result).toBe('/path/2024-03-20');
  });

  it('should combine all parameters in correct order', () => {
    const result = getDestinationPath({
      to: '/path',
      zoneId: 'FR',
      timeRange: 'hourly',
      datetime: '2024-03-20',
    });
    expect(result).toBe('/path/FR/hourly/2024-03-20');
  });

  it('should handle missing middle parameters', () => {
    const result = getDestinationPath({
      to: '/path',
      zoneId: 'FR',
      datetime: '2024-03-20',
    });
    expect(result).toBe('/path/FR/2024-03-20');
  });
});

// Mock the router hooks
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
  useLocation: vi.fn(),
  useMatch: vi.fn(),
  useMatches: vi.fn(),
  useParams: vi.fn(),
}));

describe('useNavigateWithParameters', () => {
  let navigateMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Setup default mocks
    navigateMock = vi.fn();
    (useNavigate as any).mockReturnValue(navigateMock);
    (useParams as any).mockReturnValue({
      zoneId: 'FR',
      urlTimeRange: 'hourly',
      urlDatetime: '2024-03-20T08:00:00z',
    });
    (useMatch as any).mockImplementation((path: any) => (path === '/map/*' ? {} : null));
    (useLocation as any).mockReturnValue({
      search: '',
      hash: '',
    });
    // Add useMatches mock with default return value
    (useMatches as any).mockReturnValue([{ pathname: '/map/hourly' }]);
  });

  it('should preserve existing query parameters', () => {
    (useLocation as any).mockReturnValue({
      search: '?filter=renewable&view=list',
      hash: '',
    });

    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({ to: '/map' });

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/map/hourly/2024-03-20T08:00:00z',
      search: '?filter=renewable&view=list',
      hash: '',
    });
  });

  it('should preserve existing hash', () => {
    (useLocation as any).mockReturnValue({
      search: '',
      hash: '#carbon_chart',
    });

    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({ to: '/map' });

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/map/hourly/2024-03-20T08:00:00z',
      search: '',
      hash: '#carbon_chart',
    });
  });

  it('should preserve both query parameters and hash', () => {
    (useLocation as any).mockReturnValue({
      search: '?filter=renewable',
      hash: '#details',
    });

    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({ to: '/zone', zoneId: 'DK-DK2', datetime: '2024-03-20T08:00:00z' });

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/zone/DK-DK2/hourly/2024-03-20T08:00:00z',
      search: '?filter=renewable',
      hash: '#details',
    });
  });

  it('should use previous parameters when not provided', () => {
    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({});

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/map/hourly/2024-03-20T08:00:00z',
      search: '',
      hash: '',
    });
  });

  it('Should navigate to the correct path with all parameters', () => {
    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({
      to: '/zone',
      zoneId: 'DE',
      timeRange: 'daily',
      datetime: '2024-03-21',
    });

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/zone/DE/daily/2024-03-21',
      search: '',
      hash: '',
    });
  });
  it('Should navigate to the correct path with blank datetime', () => {
    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({
      to: '/zone',
      zoneId: 'DE',
      timeRange: 'daily',
      datetime: '',
    });

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/zone/DE/daily',
      search: '',
      hash: '',
    });
  });

  it('should redirect to map when nothing is provided', () => {
    (useMatch as any).mockImplementation((path: any) =>
      path === '/zone/FR/hourly/2024-03-20T08:00:00z' ? {} : null
    );

    const { result } = renderHook(() => useNavigateWithParameters());
    result.current({});

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/map/hourly/2024-03-20T08:00:00z',
      search: '',
      hash: '',
    });
  });
});

describe('getNetExchange', () => {
  it('should return NaN when zoneData.exchange is empty', () => {
    const zoneData = {
      exchange: {},
      totalImport: null,
      totalExport: null,
      totalCo2Import: null,
      totalCo2Export: null,
    } as ZoneDetail;
    const result = getNetExchange(zoneData, false);
    expect(result).toBeNaN();
  });

  it('should return NaN when displayByEmissions is false and both totalImport and totalExport are null', () => {
    const zoneData = {
      exchange: { someKey: 1 },
      totalImport: null,
      totalExport: null,
      totalCo2Import: null,
      totalCo2Export: null,
    } as unknown as ZoneDetail;
    const result = getNetExchange(zoneData, false);
    expect(result).toBeNaN();
  });

  it('should return NaN when displayByEmissions is true and both totalCo2Import and totalCo2Export are null', () => {
    const zoneData = {
      exchange: { someKey: 1 },
      totalImport: null,
      totalExport: null,
      totalCo2Import: null,
      totalCo2Export: null,
    } as unknown as ZoneDetail;
    const result = getNetExchange(zoneData, true);
    expect(result).toBeNaN();
  });

  it('should return the correct net exchange value when displayByEmissions is false and totalImport and totalExport have values', () => {
    const zoneData = {
      exchange: { someKey: 1 },
      totalImport: 100,
      totalExport: 50,
      totalCo2Import: null,
      totalCo2Export: null,
    } as unknown as ZoneDetail;
    const result = getNetExchange(zoneData, false);
    expect(result).toBe(50);
  });

  it('should return the correct net exchange value when displayByEmissions is true and totalCo2Import and totalCo2Export have values', () => {
    const zoneData = {
      exchange: { someKey: 1 },
      totalImport: null,
      totalExport: null,
      totalCo2Import: 200,
      totalCo2Export: 100,
    } as unknown as ZoneDetail;
    const result = getNetExchange(zoneData, true);
    expect(result).toBe(100);
  });
});
