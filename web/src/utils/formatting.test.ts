import { removeDuplicateSources } from 'features/panels/zone/Attribution';
import { formatCo2, formatDataSources } from './formatting';

describe('formatCo2', () => {
  it('handles grams', () => {
    const actual = formatCo2(20);
    const expected = '20 g';
    expect(actual).toBe(expected);
  });
  it('handles kilograms', () => {
    const actual = formatCo2(1000);
    const expected = '1 kg';
    expect(actual).toBe(expected);
  });
  it('handles tons', () => {
    const actual = formatCo2(1_000_000);
    const expected = '1 t';
    expect(actual).toBe(expected);
  });

  it('uses same unit as another value would', () => {
    const actual = formatCo2(23_500, 2_350_000);
    const expected = '0 t';
    expect(actual).toBe(expected);
  });

  it('adds decimals if comparing with tons', () => {
    const actual = formatCo2(200_500, 2_350_000);
    const expected = '0.2 t';
    expect(actual).toBe(expected);
  });
  it('handles kilotonnes', () => {
    const actual = formatCo2(99_000_000_000);
    const expected = '99 kt';
    expect(actual).toBe(expected);
  });
  it('handles megatonnes', () => {
    const actual = formatCo2(99_000_000_000_000);
    const expected = '99 Mt';
    expect(actual).toBe(expected);
  });
  it('handles megatonnes close to 1Gt rounding down', () => {
    const actual = formatCo2(994_000_000_000_000);
    const expected = '990 Mt';
    expect(actual).toBe(expected);
  });
  it('handles values up to 1 trillion grams, rounding up', () => {
    const actual = formatCo2(999_000_000_000_000);
    const expected = '1 Gt';
    expect(actual).toBe(expected);
  });
  it('handles values above 1 trillion', () => {
    const actual = formatCo2(6_700_000_000_000_000);
    const expected = '6.7 Gt';
    expect(actual).toBe(expected);
  });
  it('handles values petatonnes', () => {
    const actual = formatCo2(1.5e21);
    const expected = '1.5 Pt';
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
