import { removeDuplicateSources } from 'features/panels/zone/Attribution';
import { formatCo2, formatDataSources } from './formatting';

describe('formatCo2', () => {
  it('handles grams', () => {
    const actual = formatCo2(100);
    const expected = '100g';
    expect(actual).toBe(expected);
  });
  it('handles kilograms', () => {
    const actual = formatCo2(2050);
    const expected = '2kg';
    expect(actual).toBe(expected);
  });
  it('handles tons', () => {
    const actual = formatCo2(2_350_000);
    const expected = '2t';
    expect(actual).toBe(expected);
  });

  it('uses same unit as another value would', () => {
    const actual = formatCo2(2350, 2_350_000);
    const expected = '0t';
    expect(actual).toBe(expected);
  });

  it('adds decimals if comparing with tons', () => {
    const actual = formatCo2(700_350, 2_350_000);
    const expected = '0.7t';
    expect(actual).toBe(expected);
  });
  it('handles values up to 100k', () => {
    const actual = formatCo2(70_000_350_000);
    const expected = '70,000t';
    expect(actual).toBe(expected);
  });
  it('handles values up to 1 million', () => {
    const actual = formatCo2(700_003_500_000);
    const expected = '0.7Mt';
    expect(actual).toBe(expected);
  });
  it('handles values above 1 million', () => {
    const actual = formatCo2(7_000_035_000_000_000);
    const expected = '7Gt';
    expect(actual).toBe(expected);
  });
});

describe('formatDataSources', () => {
  it('handles multiple sources with en', () => {
    const input = removeDuplicateSources(
      `"electricityMap Estimation","entsoe.eu","entsoe.eu"`
    );

    const expected = 'electricityMap Estimation and entsoe.eu';

    const actual = formatDataSources(input, 'en');
    expect(actual).toBe(expected);
  });

  it('handles multiple sources in another language', () => {
    const input = removeDuplicateSources(
      `"electricityMap Estimation","entsoe.eu","entsoe.eu"`
    );

    const expected = 'electricityMap Estimation og entsoe.eu';

    const actual = formatDataSources(input, 'da');
    expect(actual).toBe(expected);
  });

  it('single source is not changed', () => {
    const input = removeDuplicateSources(`"entsoe.eu"`);

    const expected = 'entsoe.eu';

    const actual = formatDataSources(input, 'en');
    expect(actual).toBe(expected);
  });
});
