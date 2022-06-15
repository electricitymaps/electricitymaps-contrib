import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { scaleLinear } from 'd3-scale';

import { themes, shared, co2Scales } from '../helpers/themes';

export function useTheme() {
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);

  return useMemo(() => {
    const theme = brightModeEnabled ? themes.dark : themes.bright;
    const co2Scale = colorBlindModeEnabled ? co2Scales.colorblind : co2Scales.default;

    return {
      ...shared,
      ...theme,
      co2Scale,
    };
  }, [brightModeEnabled, colorBlindModeEnabled]);
}

export function useCo2ColorScale() {
  const { co2Scale } = useTheme();

  return useMemo(
    () => scaleLinear().domain(co2Scale.steps).range(co2Scale.colors).unknown('gray').clamp(true),
    [co2Scale]
  );
}
