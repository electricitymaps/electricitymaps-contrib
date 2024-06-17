import { describe, expect, it } from 'vitest';

import { filterExchanges, shouldHideExchangeIntensity } from './arrows';

const mockExchangesToExcludeZoneView = ['exchange1', 'exchange2', 'exchange4'];

const mockExchangesToExcludeCountryView = ['exchange3', 'exchange5'];

const mockExchangesResponses = {
  exchange1: { ci: 137.68, f: -44 },
  exchange2: { ci: 131.44, f: -56 },
  exchange3: { ci: 168.29, f: -55 },
  exchange4: { ci: 199.73, f: -18 },
  exchange5: { ci: 188.22, f: -11 },
  exchange6: { ci: 150.5, f: -20 },
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

describe('shouldHideExchangeIntensity', () => {
  it('should hide exported intensity if zone has an outage', () => {
    expect(shouldHideExchangeIntensity('zone1->zone2', ['zone2'], -10)).toBe(true); // zone2 is exporting
    expect(shouldHideExchangeIntensity('zone2->zone1', ['zone2'], 10)).toBe(true); // zone2 is exporting
    expect(shouldHideExchangeIntensity('zone1->zone2', ['zone2'], 10)).toBe(false); // zone2 is importing
  });
  it('should not hide intensity of zones are not having an outage', () => {
    expect(shouldHideExchangeIntensity('zone1->zone2', [], 10)).toBe(false);
    expect(shouldHideExchangeIntensity('zone1->zone2', ['zone3'], -10)).toBe(false);
  });
});
