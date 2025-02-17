import { render } from '@testing-library/react';
import { ChevronsLeftRight, Moon, Sun } from 'lucide-react';
import { describe, expect, it } from 'vitest';

import { COLORS, getThumbIcon, getTrackBackground } from './TimeSlider';

describe('getTrackBackground', () => {
  it('returns the day color when no sets are provided', () => {
    expect(getTrackBackground(false, 10)).toEqual(COLORS.LIGHT_DAY);
    expect(getTrackBackground(true, 10)).toEqual(COLORS.DARK_DAY);
  });

  it('returns a linear gradient with night time sets when sets are provided', () => {
    const sets = [
      [2, 5],
      [8, 10],
    ];
    expect(getTrackBackground(false, 10, sets)).toMatchInlineSnapshot(`
      "linear-gradient(
          90deg,
          rgb(243,244,246) 20%, rgb(209,213,219) 20%, rgb(209,213,219) 50%, rgb(243,244,246) 50%,
      rgb(243,244,246) 80%, rgb(209,213,219) 80%, rgb(209,213,219) 100%, rgb(243,244,246) 100%
        )"
    `);
  });
});

describe('getThumbIcon', () => {
  it('returns "<ChevronsLeftRight size={20} />" when no index or sets are provided', () => {
    const { container: expected } = render(
      <ChevronsLeftRight size={20} pointerEvents="none" />
    );
    const { container } = render(getThumbIcon());
    expect(container.innerHTML).toEqual(expected.innerHTML);
  });

  it.each([[10], [35]])(
    'returns "<Moon size={16} />" when the index %i is within a night time set',
    (index) => {
      const sets = [
        [7, 21],
        [30, 40],
      ];
      const { container: expected } = render(<Moon size={20} pointerEvents="none" />);
      const { container } = render(getThumbIcon(index, sets));
      expect(container.innerHTML).toEqual(expected.innerHTML);
    }
  );

  it.each([[5], [25], [50]])(
    'returns "<Sun size={20} />" when the index %i is not within a night time set',
    (index) => {
      const sets = [
        [7, 21],
        [30, 40],
      ];
      const { container: expected } = render(<Sun size={20} pointerEvents="none" />);
      const { container } = render(getThumbIcon(index, sets));
      expect(container.innerHTML).toEqual(expected.innerHTML);
    }
  );
});
