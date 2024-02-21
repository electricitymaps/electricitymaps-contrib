import { windIntensityColorScale } from './scales';

describe('windIntensityColorScale', () => {
  it('should return an array of colors', () => {
    const result = windIntensityColorScale();
    expect(Array.isArray(result)).to.be.true;
    expect(result.length).to.be.greaterThan(0);
    expect(typeof result[0]).to.eq('string');
  });
});
