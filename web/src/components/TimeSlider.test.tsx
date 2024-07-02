import { render } from '@testing-library/react';
import { FaArrowsLeftRight, FaMoon, FaSun } from 'react-icons/fa6';
import { describe, expect, it } from 'vitest';

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
  it('returns "<FaArrowsLeftRight size={14} />" when no index or sets are provided', () => {
    const { container: expected } = render(<FaArrowsLeftRight size={14} />);
    const { container } = render(getThumbIcon());
    expect(container.innerHTML).toEqual(expected.innerHTML);
  });

  it.each([[10], [35]])(
    'returns "<FaMoon size={14} />" when the index %i is within a night time set',
    (index) => {
      const sets = [
        [7, 21],
        [30, 40],
      ];
      const { container: expected } = render(<FaMoon size={14} />);
      const { container } = render(getThumbIcon(index, sets));
      expect(container.innerHTML).toEqual(expected.innerHTML);
    }
  );

  it.each([[5], [25], [50]])(
    'returns "<FaSun size={14} />" when the index %i is not within a night time set',
    (index) => {
      const sets = [
        [7, 21],
        [30, 40],
      ];
      const { container: expected } = render(<FaSun size={14} />);
      const { container } = render(getThumbIcon(index, sets));
      expect(container.innerHTML).toEqual(expected.innerHTML);
    }
  );
});
