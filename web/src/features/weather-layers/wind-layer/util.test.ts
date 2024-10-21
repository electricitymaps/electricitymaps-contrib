import { describe, expect, it } from 'vitest';

import { floorModulus, isValue } from './util';

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
