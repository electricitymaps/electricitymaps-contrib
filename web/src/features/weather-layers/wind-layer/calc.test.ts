import { round } from 'utils/helpers';
import { describe, expect, it } from 'vitest';

import { bilinearInterpolateVector, buildBounds, distort } from './calc';

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

describe('distort', () => {
  // Same constant used in distort method
  const H = Math.pow(10, -5.2);
  // Use arbritrary small threshold for comparing floats
  const isFloatClose = (a: number, b: number) => Math.abs(a - b) < Number.EPSILON * 10;

  // Mock the Maplibre GL object for testing - only need project method
  const mapMock: maplibregl.Map = {
    project: (point: [number, number]) => {
      const [lon, lat] = point;
      let returnValue = [0, 0];
      if (lon === 0 || lat === 0) {
        // Custom case - return friendly value that we choose
        returnValue = [-H, -H];
      } else if (isFloatClose(lat, 11.825_461_358_611_037)) {
        // Real case - taken from actual Mapbox
        returnValue = [1437.999_949_237_546_4, 763.999_999_999_996_1];
      } else if (isFloatClose(lat, 11.825_455_049_037_592)) {
        // Real case - taken from actual Mapbox
        returnValue = [1437.999_999_999_982, 764.000_051_863_153_1];
      } else {
        throw new Error(`mock project function not implemented for [ ${lon}, ${lat} ]`);
      }
      return { x: returnValue[0], y: returnValue[1] };
    },
  } as unknown as maplibregl.Map;

  it('test actual case', () => {
    const [u, v, m] = distort(
      mapMock,
      95.772_609_766_159_29,
      11.825_461_358_611_037,
      1438,
      764,
      0.006_120_000_000_000_000_4,
      [0.551_289_441_234_658_4, -0.174_103_992_708_016_4, 11.492_476_595_423_65]
    );
    expect(isFloatClose(u, 0.027_732_572_562_027_27)).toBe(true);
    expect(isFloatClose(v, 0.008_758_287_040_257)).toBe(true);
    expect(isFloatClose(m, 11.492_476_595_423_65)).toBe(true);
  });

  it('test custom project', () => {
    const result = distort(mapMock, 0, 0, 0, 0, 1, [1, 1, 1]);
    // This result is mainly used as reference for following tests
    expect(result).toEqual([2, 2, 1]);
  });

  it('test scale using custom project', () => {
    const result = distort(mapMock, 0, 0, 0, 0, 2, [1, 1, 3]);
    expect(result).toEqual([4, 4, 3]);
  });

  it('test non-zero x and y bounds using custom project', () => {
    const result = distort(mapMock, 0, 0, -H, -H, 1, [1, 1, 7]);
    expect(result).toEqual([-0, -0, 7]);
  });
});

describe('buildBounds', () => {
  it('build expected bounds fields in standard case', () => {
    const bounds = [
      [0, 0],
      [821, 765],
    ];
    const width = 821;
    const height = 765;
    const result = buildBounds(bounds, width, height);

    expect(result).toEqual({ x: 0, y: 0, yMax: 764, width: 821, height: 765 });
  });

  it('handles unexpected dimension values', () => {
    const bounds = [
      [1, -10],
      [100, 101],
    ];
    const width = 100;
    const height = 50;
    const result = buildBounds(bounds, width, height);

    expect(result).toEqual({ x: 1, y: 0, yMax: 49, width: 100, height: 50 });
  });

  it('handles decimals', () => {
    const bounds = [
      [1.4, 2.6],
      [7.2, 9.5],
    ];
    const width = 5.8;
    const height = 6.9;
    const result = buildBounds(bounds, width, height);

    expect(result).toEqual({ x: 1, y: 2, yMax: 5.9, width: 5.8, height: 6.9 });
  });
});
