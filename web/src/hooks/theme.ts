import { scaleLinear } from 'd3-scale';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { MapTheme } from 'types';
import { colorblindModeAtom } from 'utils/state/atoms';
import { themes } from './oldThemes';
// TODO: Convert this to a Jotai atom and consider if we want to do things differently now with new setup
export function useTheme(): MapTheme {
  const [isColorBlindModeEnabled] = useAtom(colorblindModeAtom);
  const darkThemeMediaQuery = window.matchMedia('(prefers-color-scheme: light)');
  const isBrightModeEnabled = darkThemeMediaQuery.matches;

  return useMemo(() => {
    if (isBrightModeEnabled) {
      return isColorBlindModeEnabled ? themes.colorblindBright : themes.bright;
    } else {
      return isColorBlindModeEnabled ? themes.colorblindDark : themes.dark;
    }
  }, [isBrightModeEnabled, isColorBlindModeEnabled]) as MapTheme;
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
