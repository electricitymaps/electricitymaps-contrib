import { scaleLinear } from 'd3-scale';
import { range } from 'lodash';

// TODO: Merge themes and scales
import { themes } from './themes';

const uniformSpread = ({ from, to, count }) => (
  range(count).map(index => (from + (to - from) * index / (count - 1)))
);

// ** Wind
export const windColor = scaleLinear()
  .domain(uniformSpread({ from: 0, to: 15, count: 10 }))
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
  ])
  .clamp(true);


// ** Solar
export const solarColor = scaleLinear()
  .domain(uniformSpread({ from: 0, to: 1000, count: 3 }))
  .range(['black', 'white', 'gold'])
  .clamp(true);

// ** CO2
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
