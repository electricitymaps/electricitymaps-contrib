import { scaleLinear, scaleQuantize } from 'd3-scale';

export const quantizedCo2IntensityScale = scaleQuantize()
  .domain([0, 800])
  .range([0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800])
  .unknown('nan');

export const quantizedExchangeSpeedScale = scaleLinear()
  .domain([500, 5000])
  .rangeRound([0, 2])
  .unknown(0)
  .clamp(true);
