import { scaleLinear } from 'd3-scale';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { MapTheme } from 'types';
import { colors } from './colors';
import { colorblindModeAtom, themeAtom } from 'utils/state/atoms';
import { ThemeOptions } from 'utils/constants';
import { useMediaQuery } from 'utils';

/**
 * This hook listens for changes to the selected theme or system appearance preferences
 * @returns boolean indicating if dark mode should be used or not
 */
export function useDarkMode() {
  const [selectedTheme] = useAtom(themeAtom);
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const shouldUseDarkMode =
    selectedTheme === ThemeOptions.DARK ||
    (selectedTheme === ThemeOptions.SYSTEM && prefersDarkMode);

  return shouldUseDarkMode;
}

// TODO: Convert this to a Jotai atom and consider if we want to do things differently now with new setup
export function useTheme(): MapTheme {
  const [isColorBlindModeEnabled] = useAtom(colorblindModeAtom);
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
