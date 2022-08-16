import { useMemo } from 'react';
import { useSelector } from 'react-redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-s... Remove this comment to see the full error message
import { scaleLinear } from 'd3-scale';

import { themes } from '../helpers/themes';

export function useTheme() {
  const brightModeEnabled = useSelector((state) => (state as any).application.brightModeEnabled);
  const colorBlindModeEnabled = useSelector((state) => (state as any).application.colorBlindModeEnabled);

  return useMemo(() => {
    if (brightModeEnabled) {
      return colorBlindModeEnabled ? themes.colorblindBright : themes.bright;
    } else {
      return colorBlindModeEnabled ? themes.colorblindDark : themes.dark;
    }
  }, [brightModeEnabled, colorBlindModeEnabled]);
}

export function useCo2ColorScale() {
  const theme = useTheme();

  return useMemo(
    () => scaleLinear().domain(theme.co2Scale.steps).range(theme.co2Scale.colors).unknown('gray').clamp(true),
    [theme]
  );
}
