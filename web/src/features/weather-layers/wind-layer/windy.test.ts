import { describe, expect, it } from 'vitest';

import { windIntensityColorScale } from './scales';

describe('windIntensityColorScale', () => {
  it('should return an array of colors', () => {
    const result = windIntensityColorScale();
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThan(0);
    expect(typeof result[0]).toEqual('string');
  });
});
