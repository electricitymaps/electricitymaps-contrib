import { scaleLinear } from 'd3-scale';
import { useAtomValue } from 'jotai';
import { useMemo } from 'react';
import { MapTheme } from 'types';
import { useMediaQuery } from 'utils';
import { ThemeOptions } from 'utils/constants';
import { colorblindModeAtom, themeAtom } from 'utils/state/atoms';

import { colors } from './colors';

/**
 * This hook listens for changes to the selected theme or system appearance preferences
 * @returns boolean indicating if dark mode should be used or not
 */
export function useDarkMode() {
  const selectedTheme = useAtomValue(themeAtom);
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const shouldUseDarkMode =
    selectedTheme === ThemeOptions.DARK ||
    (selectedTheme === ThemeOptions.SYSTEM && prefersDarkMode);

  return shouldUseDarkMode;
}

// TODO: Convert this to a Jotai atom and consider if we want to do things differently now with new setup
export function useTheme(): MapTheme {
  const isColorBlindModeEnabled = useAtomValue(colorblindModeAtom);
  const isDarkModeEnabled = useDarkMode();

  return useMemo(() => {
    if (isDarkModeEnabled) {
      return isColorBlindModeEnabled ? colors.colorblindDark : colors.dark;
    } else {
      return isColorBlindModeEnabled ? colors.colorblindBright : colors.bright;
    }
  }, [isDarkModeEnabled, isColorBlindModeEnabled]) as MapTheme;
}

export function useCo2ColorScale() {
  const theme = useTheme();
  return useMemo(() => getCo2ColorScale(theme), [theme]);
}

export function getCo2ColorScale(theme: MapTheme) {
  return scaleLinear<string>()
    .domain(theme.co2Scale.steps)
    .range(theme.co2Scale.colors)
    .unknown(theme.clickableFill)
    .clamp(true);
}

export function usePriceColorScale() {
  const theme = useTheme();
  return useMemo(() => getPriceColorScale(theme), [theme]);
}

export function getPriceColorScale(theme: MapTheme) {
  return scaleLinear<string>()
    .domain(theme.priceScale.steps)
    .range(theme.priceScale.colors)
    .unknown(theme.clickableFill)
    .clamp(true);
}
