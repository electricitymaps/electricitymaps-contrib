import { scaleLinear } from 'd3-scale';
import { MapTheme } from 'types';
import { MapColorSource } from 'utils/constants';

function generateCo2Scale(cleanest: number, dirtiest: number, unknownColor: string) {
  return scaleLinear<string>()
    .domain(
      [0, 150, 600, 800, 1100, 1500].map(
        (value) => (value / 1500) * (dirtiest - cleanest) + cleanest
      )
    )
    .range(['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02', '#000'])
    .unknown(unknownColor)
    .clamp(true);
}

function generateColorblindScale(
  cleanest: number,
  dirtiest: number,
  unknownColor: string
) {
  const steps = [0, 150, 600, 800, 1100, 1500].map(
    (value) => (value / 1500) * (dirtiest - cleanest) + cleanest
  );
  return scaleLinear<string>()
    .domain(steps)
    .range(['#FFFFB0', '#E3BF66', '#BB833C', '#8B4D2B', '#4E241F', '#000'])
    .unknown(unknownColor)
    .clamp(true);
}

interface Colors {
  colorblindDark: MapTheme;
  dark: MapTheme;
  colorblindBright: MapTheme;
  bright: MapTheme;
}
export const colors: Colors = {
  colorblindDark: {
    colorScale: {
      [MapColorSource.CARBON_INTENSITY]: generateColorblindScale(0, 1500, '#7A878D'),
      [MapColorSource.RENEWABLE_PERCENTAGE]: generateColorblindScale(100, 0, '#7A878D'),
    },
    oceanColor: '#343D4C',
    strokeWidth: 0.15,
    strokeColor: '#6D6D6D',
    clickableFill: '#7A878D',
    stateBorderColor: '#d1d5db',
    nonClickableFill: '#7A878D',
  },
  dark: {
    colorScale: {
      [MapColorSource.CARBON_INTENSITY]: generateCo2Scale(0, 1500, '#7A878D'),
      [MapColorSource.RENEWABLE_PERCENTAGE]: generateCo2Scale(100, 0, '#7A878D'),
    },
    oceanColor: '#262626',
    strokeWidth: 0.15,
    strokeColor: '#6D6D6D',
    stateBorderColor: '#d1d5db',
    clickableFill: '#7A878D',
    nonClickableFill: '#7A878D',
  },
  colorblindBright: {
    colorScale: {
      [MapColorSource.CARBON_INTENSITY]: generateColorblindScale(0, 1500, '#D4D9DE'),
      [MapColorSource.RENEWABLE_PERCENTAGE]: generateColorblindScale(100, 0, '#D4D9DE'),
    },
    oceanColor: '#FAFAFA',
    strokeWidth: 0.15,
    strokeColor: '#FAFAFA',
    stateBorderColor: '#d1d5db',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
  bright: {
    colorScale: {
      [MapColorSource.CARBON_INTENSITY]: generateCo2Scale(0, 1500, '#D4D9DE'),
      [MapColorSource.RENEWABLE_PERCENTAGE]: generateCo2Scale(100, 0, '#D4D9DE'),
    },
    oceanColor: '#FAFAFA',
    strokeWidth: 0.15,
    strokeColor: '#FAFAFA',
    stateBorderColor: '#d1d5db',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
};
