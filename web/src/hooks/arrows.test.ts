import { describe, expect, it } from 'vitest';

import { filterExchanges } from './arrows';

const mockExchangesToExcludeZoneView = ['exchange1', 'exchange2', 'exchange4'];

const mockExchangesToExcludeCountryView = ['exchange3', 'exchange5'];

const mockExchangesResponses = {
  exchange1: {
    '2024-01-31T12:00:00Z': { co2intensity: 137.68, netFlow: -44 },
    '2024-01-31T13:00:00Z': { co2intensity: 133.44, netFlow: -57 },
  },
  exchange2: {
    '2024-01-31T14:00:00Z': { co2intensity: 131.44, netFlow: -56 },
    '2024-01-31T15:00:00Z': { co2intensity: 135.82, netFlow: -55 },
  },
  exchange3: {
    '2024-01-31T16:00:00Z': { co2intensity: 168.29, netFlow: -55 },
    '2024-01-31T17:00:00Z': { co2intensity: 199.8, netFlow: -13 },
  },
  exchange4: {
    '2024-01-31T18:00:00Z': { co2intensity: 199.73, netFlow: -18 },
    '2024-01-31T19:00:00Z': { co2intensity: 195.2, netFlow: -18 },
  },
  exchange5: {
    '2024-01-31T20:00:00Z': { co2intensity: 188.22, netFlow: -11 },
    '2024-01-31T21:00:00Z': { co2intensity: 178.86, netFlow: -50 },
  },
  exchange6: {
    '2024-01-31T22:00:00Z': { co2intensity: 150.5, netFlow: -20 },
    '2024-01-31T23:00:00Z': { co2intensity: 140.7, netFlow: -30 },
  },
};

const expectedAfterZoneViewFilter = {
  exchange3: mockExchangesResponses.exchange3,
  exchange5: mockExchangesResponses.exchange5,
  exchange6: mockExchangesResponses.exchange6,
};

const expectedAfterCountryViewFilter = {
  exchange1: mockExchangesResponses.exchange1,
  exchange2: mockExchangesResponses.exchange2,
  exchange4: mockExchangesResponses.exchange4,
  exchange6: mockExchangesResponses.exchange6,
};

const expectedAfterNoZone = {
  exchange1: mockExchangesResponses.exchange1,
  exchange2: mockExchangesResponses.exchange2,
  exchange4: mockExchangesResponses.exchange4,
  exchange6: mockExchangesResponses.exchange6,
};

const expectedAfterNoCountryViewFilter = {
  exchange3: mockExchangesResponses.exchange3,
  exchange5: mockExchangesResponses.exchange5,
  exchange6: mockExchangesResponses.exchange6,
};

describe('filterExchanges', () => {
  it('should return the correct exchanges for a zone filter', () => {
    expect(
      filterExchanges(
        mockExchangesResponses,
        mockExchangesToExcludeZoneView,
        mockExchangesToExcludeCountryView
      )
    ).toEqual([expectedAfterZoneViewFilter, expectedAfterCountryViewFilter]);
  });

  it('should return empty objects if no exchanges are passed', () => {
    expect(
      filterExchanges(
        {},
        mockExchangesToExcludeZoneView,
        mockExchangesToExcludeCountryView
      )
    ).toEqual([{}, {}]);
  });

  describe('should return all zones for a type if no filter was passed', () => {
    it('no zone filter', () => {
      expect(
        filterExchanges(mockExchangesResponses, [], mockExchangesToExcludeCountryView)
      ).toEqual([mockExchangesResponses, expectedAfterNoZone]);
    });

    it('no country filter', () => {
      expect(
        filterExchanges(mockExchangesResponses, mockExchangesToExcludeZoneView, [])
      ).toEqual([expectedAfterNoCountryViewFilter, mockExchangesResponses]);
    });
  });

  it('should throw an error if exchanges is not an object', () => {
    expect(() =>
      filterExchanges(
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore This is deliberately passing a non-object to test the function.
        null,
        mockExchangesToExcludeZoneView,
        mockExchangesToExcludeCountryView
      )
    ).toThrow(TypeError);

    expect(() =>
      filterExchanges(
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore This is deliberately passing a non-object to test the function.
        undefined,
        mockExchangesToExcludeZoneView,
        mockExchangesToExcludeCountryView
      )
    ).toThrow(TypeError);
  });

  describe('should throw an error if exclusions is not an iterable', () => {
    const nonIterable = {};
    it('no iterable zone filter', () => {
      expect(() =>
        filterExchanges(
          mockExchangesResponses,
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore This is deliberately passing a non-iterable to test the function.
          nonIterable,
          mockExchangesToExcludeCountryView
        )
      ).toThrow(TypeError);
    });

    it('no iterable country filter', () => {
      expect(() =>
        filterExchanges(
          mockExchangesResponses,
          mockExchangesToExcludeZoneView,
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore This is deliberately passing a non-iterable to test the function.
          nonIterable
        )
      ).toThrow(TypeError);
    });
  });
});
