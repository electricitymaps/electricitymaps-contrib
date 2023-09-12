import { round } from 'utils/helpers';

import { bilinearInterpolateVector, windIntensityColorScale } from './windy';
describe('windIntensityColorScale', () => {
  it('should return an array of colors', () => {
    const result = windIntensityColorScale();
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThan(0);
    expect(typeof result[0]).toBe('string');
  });
});

describe('bilinearInterpolateVector', () => {
  it('should interpolate a vector at the center of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0.5;
    const y = 0.5;
    const [result1, result2, result3] = bilinearInterpolateVector(
      x,
      y,
      g00,
      g10,
      g01,
      g11
    );
    const result = [result1, result2, round(result3, 13)];
    expect(result).toEqual([4, 5, round(Math.sqrt(41), 13)]);
  });

  it('should interpolate a vector at the top left corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0;
    const y = 0;
    const [result1, result2, result3] = bilinearInterpolateVector(
      x,
      y,
      g00,
      g10,
      g01,
      g11
    );
    const result = [result1, result2, round(result3, 13)];
    expect(result).toEqual([1, 2, round(Math.sqrt(5), 13)]);
  });

  it('should interpolate a vector at the top right corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 1;
    const y = 0;
    const [result1, result2, result3] = bilinearInterpolateVector(
      x,
      y,
      g00,
      g10,
      g01,
      g11
    );
    const result = [result1, result2, round(result3, 13)];
    expect(result).toEqual([3, 4, 5]);
  });

  it('should interpolate a vector at the bottom left corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0;
    const y = 1;
    const [result1, result2, result3] = bilinearInterpolateVector(
      x,
      y,
      g00,
      g10,
      g01,
      g11
    );
    const result = [result1, result2, round(result3, 13)];
    expect(result).toEqual([5, 6, round(Math.sqrt(61), 13)]);
  });

  it('should interpolate a vector at the bottom right corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 1;
    const y = 1;
    const [result1, result2, result3] = bilinearInterpolateVector(
      x,
      y,
      g00,
      g10,
      g01,
      g11
    );
    const result = [result1, result2, round(result3, 13)];
    expect(result).toEqual([7, 8, round(Math.sqrt(113), 13)]);
  });
});
