import { bilinearInterpolateVector } from './windy';

describe('bilinearInterpolateVector', () => {
  it('should interpolate a vector at the center of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0.5;
    const y = 0.5;
    const result = bilinearInterpolateVector(x, y, g00, g10, g01, g11);
    expect(result).toEqual([4, 5, Math.sqrt(41)]);
  });

  it('should interpolate a vector at the top left corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0;
    const y = 0;
    const result = bilinearInterpolateVector(x, y, g00, g10, g01, g11);
    expect(result).toEqual([1, 2, Math.sqrt(5)]);
  });

  it('should interpolate a vector at the top right corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 1;
    const y = 0;
    const result = bilinearInterpolateVector(x, y, g00, g10, g01, g11);
    expect(result).toEqual([3, 4, 5]);
  });

  it('should interpolate a vector at the bottom left corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 0;
    const y = 1;
    const result = bilinearInterpolateVector(x, y, g00, g10, g01, g11);
    expect(result).toEqual([5, 6, Math.sqrt(61)]);
  });

  it('should interpolate a vector at the bottom right corner of the square', () => {
    const g00 = [1, 2];
    const g10 = [3, 4];
    const g01 = [5, 6];
    const g11 = [7, 8];
    const x = 1;
    const y = 1;
    const result = bilinearInterpolateVector(x, y, g00, g10, g01, g11);
    expect(result).toEqual([7, 8, Math.sqrt(113)]);
  });
});
