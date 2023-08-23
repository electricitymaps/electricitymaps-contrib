import { removeDuplicateSources } from 'features/panels/zone/Attribution';
import { formatCo2, formatDataSources } from './formatting';

describe('formatCo2', () => {
  it('handles grams', () => {
    const actual = formatCo2(1200);
    const expected = '20g';
    expect(actual).toBe(expected);
  });
  it('handles kilograms', () => {
    const actual = formatCo2(60_950);
    const expected = '1kg';
    expect(actual).toBe(expected);
  });
  it('handles tons', () => {
    const actual = formatCo2(60_950_000);
    const expected = '1t';
    expect(actual).toBe(expected);
  });

  it('uses same unit as another value would', () => {
    const actual = formatCo2(23_500, 2_350_000);
    const expected = '0t';
    expect(actual).toBe(expected);
  });

  it('adds decimals if comparing with tons', () => {
    const actual = formatCo2(12_003_500, 200_350_000);
    const expected = '0.2t';
    expect(actual).toBe(expected);
  });
  it('handles values up to 100k', () => {
    const actual = formatCo2(700_003_500_000);
    const expected = '11,667t';
    expect(actual).toBe(expected);
  });
  it('handles values up to 1 million', () => {
    const actual = formatCo2(30_000_035_000_000);
    const expected = '0.5Mt';
    expect(actual).toBe(expected);
  });
  it('handles values above 1 million', () => {
    const actual = formatCo2(400_000_350_000_000_000);
    const expected = '6.7Gt';
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
