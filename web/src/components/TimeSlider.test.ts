import { getThumbIcon, getTrackBackground, COLORS } from './TimeSlider';

describe('getTrackBackground', () => {
  it('returns the day color when no sets are provided', () => {
    expect(getTrackBackground(false, 10)).toEqual(COLORS.light.day);
    expect(getTrackBackground(true, 10)).toEqual(COLORS.dark.day);
  });

  it('returns a linear gradient with night time sets when sets are provided', () => {
    const sets = [
      [2, 5],
      [8, 10],
    ];
    const expectedBackground = `linear-gradient(\n    90deg,\n    rgb(243,244,246) 20%, rgb(209,213,219) 20%, rgb(209,213,219) 50%, rgb(243,244,246) 50%,\nrgb(243,244,246) 80%, rgb(209,213,219) 80%, rgb(209,213,219) 100%, rgb(243,244,246) 100%\n  )`;
    expect(getTrackBackground(false, 10, sets)).toEqual(expectedBackground);
  });
});

describe('getThumbIcon', () => {
  it('returns "slider-thumb.svg" when no index or sets are provided', () => {
    expect(getThumbIcon()).toEqual('slider-thumb.svg');
  });

  it('returns "slider-thumb-night.svg" when the index is within a night time set', () => {
    const sets = [
      [7, 21],
      [30, 40],
    ];
    expect(getThumbIcon(10, sets)).toEqual('slider-thumb-night.svg');
    expect(getThumbIcon(35, sets)).toEqual('slider-thumb-night.svg');
  });

  it('returns "slider-thumb-day.svg" when the index is not within a night time set', () => {
    const sets = [
      [7, 21],
      [30, 40],
    ];
    expect(getThumbIcon(5, sets)).toEqual('slider-thumb-day.svg');
    expect(getThumbIcon(25, sets)).toEqual('slider-thumb-day.svg');
    expect(getThumbIcon(50, sets)).toEqual('slider-thumb-day.svg');
  });
});
