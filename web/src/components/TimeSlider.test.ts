import { expect } from 'vitest';

import { COLORS, getThumbIcon, getTrackBackground } from './TimeSlider';

describe('getTrackBackground', () => {
  it('returns the day color when no sets are provided', () => {
    expect(getTrackBackground(false, 10)).to.eq(COLORS.light.day);
    expect(getTrackBackground(true, 10)).to.eq(COLORS.dark.day);
  });

  it('returns a linear gradient with night time sets when sets are provided', () => {
    const sets = [
      [2, 5],
      [8, 10],
    ];
    expect(getTrackBackground(false, 10, sets)).toMatchInlineSnapshot(`
      "linear-gradient(
          90deg,
          rgba(229, 231, 235, 0.5) 20%, rgba(75, 85, 99, 0.5) 20%, rgba(75, 85, 99, 0.5) 50%, rgba(229, 231, 235, 0.5) 50%,
      rgba(229, 231, 235, 0.5) 80%, rgba(75, 85, 99, 0.5) 80%, rgba(75, 85, 99, 0.5) 100%, rgba(229, 231, 235, 0.5) 100%
        )"
    `);
  });
});

describe('getThumbIcon', () => {
  it('returns "slider-thumb.svg" when no index or sets are provided', () => {
    expect(getThumbIcon()).to.eq('slider-thumb.svg');
  });

  it('returns "slider-thumb-night.svg" when the index is within a night time set', () => {
    const sets = [
      [7, 21],
      [30, 40],
    ];
    expect(getThumbIcon(10, sets)).to.eq('slider-thumb-night.svg');
    expect(getThumbIcon(35, sets)).to.eq('slider-thumb-night.svg');
  });

  it('returns "slider-thumb-day.svg" when the index is not within a night time set', () => {
    const sets = [
      [7, 21],
      [30, 40],
    ];
    expect(getThumbIcon(5, sets)).to.eq('slider-thumb-day.svg');
    expect(getThumbIcon(25, sets)).to.eq('slider-thumb-day.svg');
    expect(getThumbIcon(50, sets)).to.eq('slider-thumb-day.svg');
  });
});
