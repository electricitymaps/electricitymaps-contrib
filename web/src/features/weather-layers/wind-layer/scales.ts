import { range } from 'd3-array';
import { interpolate } from 'd3-interpolate';
import { scaleLinear } from 'd3-scale';

const MAX_WIND = 15;

export const windColor = scaleLinear<string>()
  .domain(range(10).map((index) => interpolate(0, MAX_WIND)(index / (10 - 1))))
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
