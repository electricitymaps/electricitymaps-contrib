import { GridState } from 'types';
import { describe, expect, it } from 'vitest';

import { getRankedState } from './getRankingPanelData';

const data = {
  datetimes: {
    datetimeIndex: {
      z: {
        zone1: { p: { ci: 10 }, c: { ci: 10 } },
        zone2: { p: { ci: 5 }, c: { ci: 5 } },
        zone3: { p: { ci: undefined }, c: { ci: undefined } },
        zone4: { p: { ci: 15 }, c: { ci: 15 } },
        zone5: { p: { ci: Number.NaN }, c: { ci: Number.NaN } },
        zone6: { p: { ci: 25 }, c: { ci: 25 } },
        zone7: { p: { ci: null }, c: { ci: null } },
        zone8: { p: { ci: 25 }, c: { ci: 25 } },
      },
    },
  },
} as unknown as GridState;

describe('getRankedState', () => {
  it('returns an empty array if data is undefined', () => {
    const actual = getRankedState(
      undefined,
      () => 'color',
      'asc',
      'datetimeIndex',
      true,
      'spatialAggregation'
    );
    expect(actual).toEqual([]);
  });

  it('returns an empty array if gridState or gridState.z is undefined', () => {
    const data = {
      datetimes: {
        datetimeIndex: {},
      },
    } as unknown as GridState;
    const actual = getRankedState(
      data,
      () => 'color',
      'asc',
      'datetimeIndex',
      true,
      'spatialAggregation'
    );
    expect(actual).toEqual([]);
  });

  it('sorts the zones by carbon intensity in ascending order', () => {
    const actual = getRankedState(
      data,
      () => 'color',
      'asc',
      'datetimeIndex',
      true,
      'spatialAggregation'
    );
    expect(actual).toMatchSnapshot();
  });

  it('sorts the zones by carbon intensity in descending order', () => {
    const actual = getRankedState(
      data,
      () => 'color',
      'desc',
      'datetimeIndex',
      true,
      'spatialAggregation'
    );
    expect(actual).toMatchSnapshot();
  });
});
