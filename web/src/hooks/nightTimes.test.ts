import { describe, expect, it } from 'vitest';

import { calculateNightTimes } from './nightTimes';

function createDatetimes(start: Date) {
  const datetimes = [];
  for (let index = 0; index <= 24; index++) {
    datetimes.push(new Date(start.getTime() + index * 60 * 60 * 1000));
  }
  return datetimes;
}

describe('calculateNightTimes', () => {
  it('should handle a single night during the period', () => {
    const datetimes = createDatetimes(new Date('2023-06-01T02:00:00'));
    const latitude = -38.253;
    const longitude = 146.575;
    const result = calculateNightTimes(datetimes, latitude, longitude);
    expect(result).toEqual([[7, 21]]);
  });
  it('should handle multiple nights during the period', () => {
    const datetimes = createDatetimes(new Date('2023-06-01T12:00:00'));
    const latitude = -38.253;
    const longitude = 146.575;
    const result = calculateNightTimes(datetimes, latitude, longitude);
    expect(result).toEqual([
      [0, 11],
      [21, 24],
    ]);
  });
});
