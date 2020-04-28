import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { scaleLinear } from 'd3-scale';

import { themes } from '../helpers/themes';

export function useTheme() {
  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);

  return useMemo(
    () => (brightModeEnabled ? themes.bright : themes.dark),
    [brightModeEnabled],
  );
}

export function useCo2ColorScale() {
  const colorBlindModeEnabled = useSelector(state => state.application.colorBlindModeEnabled);

  return useMemo(
    () => {
      const theme = colorBlindModeEnabled
        ? themes.colorblindScale
        : themes.co2Scale;
      return scaleLinear()
        .domain(theme.steps)
        .range(theme.colors)
        .unknown('gray')
        .clamp(true);
    },
    [colorBlindModeEnabled],
  );
}
