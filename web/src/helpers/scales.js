import { scaleLinear, scaleQuantize } from 'd3-scale';
import { range } from 'd3-array';
import { interpolate } from 'd3-interpolate';

// ** Wind
const maxWind = 15;
export const windColor = scaleLinear()
  .domain(range(10).map((i) => interpolate(0, maxWind)(i / (10 - 1))))
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
export const solarColor = scaleLinear().domain([0, 500, 1000]).range(['black', 'transparent', 'gold']).clamp(true);

// ** Exchange

export const quantizedCo2IntensityScale = scaleQuantize()
  .domain([0, 800])
  .range([0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800])
  .unknown('nan');

export const quantizedExchangeSpeedScale = scaleLinear().domain([500, 5000]).rangeRound([0, 2]).unknown(0).clamp(true);
