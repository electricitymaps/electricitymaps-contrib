import { Capacitor } from '@capacitor/core';
import { describe, expect, it } from 'vitest';

import { floorModulus, isIphone, isMobile, isValue } from './util';

describe('isValue', () => {
  it.each([
    { input: null, expected: false },
    { input: undefined, expected: false },
    { input: 0, expected: true },
    { input: '', expected: true },
    { input: 'a', expected: true },
    { input: {}, expected: true },
    { input: [], expected: true },
    { input: true, expected: true },
    { input: false, expected: true },
    { input: Number.NaN, expected: true },
    { input: 1, expected: true },
  ])('should return $expected if the value is $input', ({ input, expected }) => {
    expect(isValue(input)).toEqual(expected);
  });
});

describe('floorModulus', () => {
  it.each([
    { a: 5, n: 3, expected: 2 },
    { a: -5, n: 3, expected: 1 },
    { a: 5, n: -3, expected: -1 },
    { a: -5, n: -3, expected: -2 },
    { a: 10, n: 2, expected: 0 },
    { a: 10, n: 3, expected: 1 },
    { a: 0, n: 3, expected: 0 },
    { a: 3, n: 3, expected: 0 },
    { a: -3, n: 3, expected: 0 },
    { a: 3, n: -3, expected: 0 },
    { a: -3, n: -3, expected: 0 },
  ])('should return $expected when a is $a and n is $n', ({ a, n, expected }) => {
    expect(floorModulus(a, n)).toEqual(expected);
  });
});

describe('isMobile', () => {
  it.each([
    {
      userAgent:
        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
      expected: true,
    },
    {
      userAgent:
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
      expected: true,
    },
    {
      userAgent:
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
      expected: false,
    },
    {
      userAgent:
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
      expected: false,
    },
  ])('should return $expected for userAgent $userAgent', ({ userAgent, expected }) => {
    Object.defineProperty(navigator, 'userAgent', {
      value: userAgent,
      configurable: true,
    });
    expect(isMobile()).toEqual(expected);
  });
});

describe('isIphone', () => {
  it.each([
    {
      platform: 'ios',
      userAgent:
        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
      expected: true,
    },
    {
      platform: 'ios',
      userAgent:
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
      expected: true,
    },
    {
      platform: 'android',
      userAgent:
        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
      expected: true,
    },
    {
      platform: 'android',
      userAgent:
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
      expected: false,
    },
    {
      platform: 'web',
      userAgent:
        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
      expected: true,
    },
    {
      platform: 'web',
      userAgent:
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
      expected: false,
    },
  ])(
    'should return $expected for platform $platform and userAgent $userAgent',
    ({ platform, userAgent, expected }) => {
      vi.spyOn(Capacitor, 'getPlatform').mockReturnValue(platform);
      Object.defineProperty(navigator, 'userAgent', {
        value: userAgent,
        configurable: true,
      });
      expect(isIphone()).toEqual(expected);
    }
  );
});
