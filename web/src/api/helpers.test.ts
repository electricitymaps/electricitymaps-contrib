import { describe, expect, it } from 'vitest';

import { cacheBuster } from './helpers';

describe('cacheBuster', () => {
  it('should return a valid ISO string', () => {
    const result = cacheBuster();
    expect(new Date(result).toISOString()).toBe(result);
  });

  it('should round down the minutes to the nearest multiple of 5', () => {
    const mockDate = new Date('2023-01-01T12:07:45.000Z');
    vi.setSystemTime(mockDate);

    const result = cacheBuster();
    const resultDate = new Date(result);

    expect(resultDate.getMinutes()).toBe(5);
    expect(resultDate.getSeconds()).toBe(0);
    expect(resultDate.getMilliseconds()).toBe(0);
  });

  it('should set seconds and milliseconds to 0', () => {
    const mockDate = new Date('2023-01-01T12:07:45.678Z');
    vi.setSystemTime(mockDate);

    const result = cacheBuster();
    const resultDate = new Date(result);

    expect(resultDate.getSeconds()).toBe(0);
    expect(resultDate.getMilliseconds()).toBe(0);
  });
});
