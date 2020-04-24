import { scaleLinear } from 'd3-scale';
import { range } from 'lodash';

// TODO: Merge themes and scales
import { themes } from './themes';

// ** Wind
export const windColor = scaleLinear()
  .domain([0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30])
  .range([
    'rgba(0,   255, 255, 1.0)',
    'rgba(100, 240, 255, 1.0)',
    'rgba(135, 225, 255, 1.0)',
    'rgba(160, 208, 255, 1.0)',
    'rgba(181, 192, 255, 1.0)',
    'rgba(198, 173, 255, 1.0)',
    'rgba(212, 155, 255, 1.0)',
    'rgba(225, 133, 255, 1.0)',
    'rgba(236, 109, 255, 1.0)',
    'rgba(255,  30, 219, 1.0)',
    'rgba(255,  30, 219, 1.0)',
  ])
  .clamp(true);


// ** Solar
export const solarColor = scaleLinear()
  .domain([0, 500, 1000])
  .range(['black', 'transparent', 'gold'])
  .clamp(true);

// ** CO₂
export const getCo2Scale = (colorBlindModeEnabled) => {
  const theme = colorBlindModeEnabled
    ? themes.colorblindScale
    : themes.co2Scale;

  return scaleLinear()
    .domain(theme.steps)
    .range(theme.colors)
    .unknown('gray')
    .clamp(true);
};
