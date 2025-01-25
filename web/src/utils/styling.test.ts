import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useMediaQuery } from './styling';

const BELOW_MIN_WIDTH = 599;
const MIN_WITDH = 600;

describe('useMediaQuery', () => {
  it('renders', () => {
    window.resizeTo(BELOW_MIN_WIDTH, 0);
    const { result } = renderHook(() => useMediaQuery(`(min-width: ${MIN_WITDH}px)`));
    expect(result.current).toBe(false);

    act(() => window.resizeTo(MIN_WITDH, 0));

    expect(result.current).toBe(true);
  });
});
