import {
  opacityToSolarIntensity,
  solarColor,
  solarColorComponents,
  solarIntensityToOpacity,
  splitRGBA,
} from './utils';

describe('splitRGBA', () => {
  it('works with rgb()', () => {
    const result = splitRGBA('rgb(255, 0, 0)');
    expect(result).toStrictEqual([255, 0, 0, 1]);
  });
  it('works with rgba()', () => {
    const result = splitRGBA('rgb(255, 0, 0, 0.23)');
    expect(result).toStrictEqual([255, 0, 0, 0.23]);
  });
});

describe('solarColor', () => {
  it('works', () => {
    const result = solarColor(97);
    expect(result).toStrictEqual('rgba(0, 0, 0, 0.806)');
  });
});

describe('solarIntensityToOpacity', () => {
  it('works', () => {
    const result = solarIntensityToOpacity(97);
    expect(result).toStrictEqual(24);
  });
});

describe('opacityToSolarIntensity', () => {
  it('works', () => {
    const result = opacityToSolarIntensity(97);
    expect(result).toStrictEqual(380);
  });
});
describe('solarColorComponents', () => {
  it('works ', () => {
    const result = solarColorComponents[380];
    expect(result).toStrictEqual({ alpha: 52, blue: 0, green: 0, red: 0 });
  });
});
