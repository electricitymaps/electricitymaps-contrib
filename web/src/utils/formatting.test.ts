import { removeDuplicateSources } from 'features/panels/zone/Attribution';
import { formatDataSources } from './formatting';

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
